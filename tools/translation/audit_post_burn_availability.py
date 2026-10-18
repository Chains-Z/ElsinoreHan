"""只读核对烧书状态、真实界面源词及晨间对白，独立输出审计证据。"""

import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

from export_sol_full import encode
from prepare_dialogue_log_followup import (
    DIALOGUE, GAME_RESOURCE, ROOT, SCENE, dialogue_source, read, read_text_assets, save,
)


BUILD = ROOT / "runtime/build/post-burn-availability"
EVIDENCE = ROOT / "runtime/evidence/post-burn-availability-audit-2026-10-19.json"
FULL = ROOT / "translation/sol-full-2026-10-09"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replay_burnt(method, revenge, viewed):
    """严格解释原方法的布尔分支；仅替代状态读取，不运行任何游戏组件。"""
    instructions = method["il"]
    labels = {line.split(": ", 1)[0]: i for i, line in enumerate(instructions)}
    stack, locals_ = [], {}
    pc = 0
    for _ in range(100):
        instruction = instructions[pc].split(": ", 1)[1]
        pc += 1
        if instruction.startswith("ldarg.1"):
            stack.append("page")
        elif instruction.startswith("ldsfld ") and "::ENDING_REVENGE" in instruction:
            stack.append("revenge")
        elif instruction == "stloc.0":
            locals_[0] = stack.pop()
        elif instruction == "ldloc.0":
            stack.append(locals_[0])
        elif instruction.startswith("call ") and "ObjectTracker::get_Instance()" in instruction:
            stack.append("tracker")
        elif instruction.startswith("callvirt ") and any(x in instruction for x in (
            "ObjectTracker::get_Info()", "IGameInfo::get_State()", "GameState::get_Logic()",
        )):
            stack.pop()
            stack.append("state")
        elif instruction.startswith("call ") and "Atom::EndingViewed(" in instruction:
            stack.append(("viewed", stack.pop()))
        elif instruction.startswith("callvirt ") and "LogicState::IsTrue(" in instruction:
            atom = stack.pop()
            stack.pop()
            assert atom[0] == "viewed"
            stack.append(revenge if atom[1] == "revenge" else viewed)
        elif instruction.startswith("brfalse.s "):
            if not stack.pop():
                pc = labels[instruction.split(" ", 1)[1]]
        elif instruction in ("ldc.i4.0", "ldc.i4.1"):
            stack.append(instruction.endswith("1"))
        elif instruction == "ret":
            assert len(stack) == 1
            return stack.pop()
        else:
            raise ValueError("原 IL 出现未审核指令：" + instruction)
    raise ValueError("原 IL 未在限定步数内返回")


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    il = read(BUILD / "current-ui-il.json")
    for source_file in il["source_files"]:
        assert sha(Path(source_file["path"]).read_bytes()) == source_file["sha256"]
    current = {row["source"]: row for row in read(FULL / "translations.json")}
    installed_path = GAME_RESOURCE.parents[1] / "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt"
    installed_bytes = installed_path.read_bytes()
    installed = set(installed_bytes.decode("utf-8-sig").splitlines())
    assets = list(read_text_assets(GAME_RESOURCE.read_bytes()))
    endings_sha, endings_text = next((h, t) for n, h, t in assets if n == "endings" and "END_Resignation" in t)
    endings = json.loads(endings_text)["endings"]
    scene_sha, scene_text = next((h, t) for n, h, t in assets if n == "scenes" and "elif viewedEnding(END_Revenge):" in t)
    evidence_rows, cases, missing = [], [], []

    def add(source, category, origins, nonlexical=False):
        row = current.get(source)
        target = source if nonlexical else row["target"] if row else None
        entry = {"source": source, "source_sha256": sha(source.encode()), "category": category,
                 "origins": origins, "translation_id": row["id"] if row else None, "target": target,
                 "match": "nonlexical" if nonlexical else "exact" if row else "missing",
                 "installed_exact_encoded_line": None if nonlexical else encode(source) + "=" + encode(target) in installed if target else False}
        evidence_rows.append(entry)
        if target is None:
            missing.append(entry)
        else:
            cases.append({"id": "availability-" + str(len(cases) + 1), "source": source, "target": target})
        return target

    for ending in endings:
        for field in ("sacrifice-what", "sacrifice-for", "description"):
            add(ending[field], "ending_metadata", [{"asset": "endings", "asset_sha256": endings_sha,
                "ending_id": ending["id"], "field": field, "inbook": ending["inbook"]}])
    visible_calls = ("::AddText(", "::AddButton(", "::AddButtonWithDefaultCloseBehavior(", "::AddTwoHorizontalButtons(", "TMP_Text::set_text(", "Elsinore.Ui.TooltipInfo::.ctor(")
    excluded = []
    for method in il["methods"]:
        if method["type"] == "GameDataGenerated" or "AllowInteraction" in method["name"]:
            continue
        for index, line in enumerate(method["il"]):
            if ': ldstr "' not in line:
                continue
            source = line.split(': ldstr "', 1)[1][:-1]
            window = method["il"][index + 1:index + 8]
            origin = {"assembly": method["assembly"], "method": method["name"], "il_offset": line.split(": ", 1)[0]}
            if (any(any(call in item for call in visible_calls) for item in window) or source == "Choose This Ending") and source != "test\ntest\ntest":
                add(source, "assembly_visible_literal", [origin])
            else:
                excluded.append({"source": source, "origin": origin, "reason": "对象/资源/音乐标识、日志或初始化占位；无新增烧书提示"})

    static_sources = {"Choose This Fate", "Revisit this Fate", "Never Mind", "NEW FATE UNLOCKED", "Cancel", "Next Page", "Previous Page", "Destroy Book"}
    level_path = GAME_RESOURCE.parent / "level1"
    level = level_path.read_bytes()
    for row in read(ROOT / "analysis/ui-audit/resource-strings.json"):
        origin = row.get("origin", {})
        if origin.get("file") == "level1" and row["source"] in static_sources and origin.get("field") in ("m_text", "tooltip"):
            offset = origin["absolute_offset"]
            length = struct.unpack_from("<I", level, offset)[0]
            assert level[offset + 4:offset + 4 + length].decode("utf-8") == row["source"]
            add(row["source"], "serialized_static_label_or_tooltip", [{k: v for k, v in origin.items() if k not in ("ui_path", "parser")}])
    for source in ("<i>Sacrifice</i>", "<i>for</i>"):
        add(source, "paper_image_overlay", [{"contract": "translation/supplemental/ending-burnt-paper-source.json",
            "consumer": "tools/patch/TranslationToggle.cs EndingBookLabels；沿用1.5.11已安装验证"}])

    start = scene_text.index("elif viewedEnding(END_Revenge):")
    end = scene_text.index("elif (occurrenceCount", start)
    scene_name = list(SCENE.finditer(scene_text, 0, start))[-1][1]
    assert scene_name == "Spine_OpheliaHamletStarter"
    morning = []
    for match in DIALOGUE.finditer(scene_text, start, end):
        raw = json.loads('"' + match["text"] + '"')
        runtime = dialogue_source(match["actor"], raw)
        assembly_origins = [{"assembly": method["assembly"], "method": method["name"], "il_offset": line.split(": ", 1)[0]}
                            for method in il["methods"] if method["type"] == "GameDataGenerated"
                            for line in method["il"] if line.endswith(': ldstr "' + runtime + '"')]
        assert assembly_origins, "晨间运行源必须精确命中当前原程序集"
        origins = [{"asset": "scenes", "asset_sha256": scene_sha, "scene": scene_name,
                    "line": scene_text[:match.start()].count("\n") + 1, "actor": match["actor"]}] + assembly_origins
        target = add(raw, "post_burn_morning_resource", origins, raw == "...")
        runtime_target = add(runtime, "post_burn_morning_runtime", origins, runtime == "...")
        assert target == runtime_target
        name, zh_name = ("Hamlet", "哈姆雷特") if match["actor"] == "hamlet" else ("Ophelia", "奥菲莉娅")
        for source, expected in (
            ("<line-height=90%>" + runtime, "<line-height=90%>" + target),
            ("<b>" + name + ":</b> <indent=16%>" + runtime, "<b>" + zh_name + ":</b> <indent=16%>" + target),
        ):
            cases.append({"id": "availability-" + str(len(cases) + 1), "source": source, "target": expected})
        morning.append({"source": raw, "runtime_source": runtime, "target": target, "origins": origins})
    assert len(morning) == 14
    # 只组合真实可达的首次路径和四种后续随机路径，不把互斥台词拼成一条剧情。
    morning_paths = ([0, 1, 2, 8, 9, 10, 11, 12, 13], [3, 8, 9], [4, 8, 9], [5, 8, 9], [6, 7, 8, 9])
    for indexes in morning_paths:
        assembled = []
        for translated in (False, True):
            content, previous = "", None
            for index in indexes:
                row = morning[index]
                actor = row["origins"][0]["actor"]
                text = row["target"] if translated else row["runtime_source"]
                if actor == previous:
                    content += "\n" + text
                else:
                    name = ("哈姆雷特" if actor == "hamlet" else "奥菲莉娅") if translated else ("Hamlet" if actor == "hamlet" else "Ophelia")
                    content += ("</indent>\n" if previous else "") + "<b>" + name + ":</b> <indent=16%>" + text
                previous = actor
            assembled.append(content)
        cases.append({"id": "availability-morning-path-" + str(len(cases) + 1), "source": assembled[0], "target": assembled[1]})

    predicates = [row for row in il["methods"] if "::isEndingBurnt(" in row["name"]]
    assert len(predicates) == 2
    states = []
    for ending in [row for row in endings if row["inbook"]]:
        for unlocked in (False, True):
            for revenge in (False, True):
                for viewed in (False, True):
                    actual = [replay_burnt(method, revenge, viewed) for method in predicates]
                    assert actual == [revenge or viewed] * 2
                    states.append({"ending_id": ending["id"], "unlocked": unlocked, "revenge_viewed": revenge,
                                   "page_viewed": viewed, "replayed_burnt": actual[0],
                                   "revisit_visible_by_populate_il": unlocked and not actual[0],
                                   "confirm_visible_if_accessed_from_book_by_activate_il": not actual[1]})
    source_files = il["source_files"] + [
        {"path": str(GAME_RESOURCE), "sha256": sha(GAME_RESOURCE.read_bytes())},
        {"path": str(level_path), "sha256": sha(level)},
        {"path": str(FULL / "translations.json"), "sha256": sha((FULL / "translations.json").read_bytes())},
        {"path": str(FULL / "dynamic-rules.json"), "sha256": sha((FULL / "dynamic-rules.json").read_bytes())},
        {"path": str(installed_path), "sha256": sha(installed_bytes)},
    ]
    state_refs = []
    for name, digest, text in assets:
        if name == "event-html":
            continue
        for index, line in enumerate(text.splitlines(), 1):
            if "viewedEnding(END_Revenge)" in line or "shattered(quince)" in line:
                state_refs.append({"asset": name, "asset_sha256": digest, "line": index, "text": line})
    relevant = [row for row in il["methods"] if any(x in row["name"] for x in (
        "::isEndingBurnt(", "::populate(", "::Elsinore.Ui.IActivatableModalCanvas.Activate(",
        "GameOverUI::Activate(", "EndingBookObject::Initialize(", "EndingSelectUI/<>c::<Elsinore.Ui.IActivatableModalCanvas.Activate>",
        "EndingBookObject::Interact(", "AllowInteraction",
    ))]
    visible_labels = {row["source"] for row in evidence_rows}
    assert static_sources <= visible_labels
    assert {"Choose This Ending", "Hand of Dionysus", "<i>This world has not yet come to pass.</i>"} <= visible_labels
    report = {"schema_version": 1, "date": "2026-10-19", "scope": "只读资源与程序集、原IL布尔分支重放、真实XUnity离线文字消费者；未启动游戏、未读取或修改玩家存档、未安装",
              "source_files": source_files, "endings_asset_sha256": endings_sha, "scenes_asset_sha256": scene_sha,
              "key_methods": relevant, "state_references": state_refs, "visible_sources": evidence_rows,
              "excluded_literals": excluded, "morning_dialogue": morning, "state_matrix": states,
              "summary": {"ordinary_pages": 11, "all_endings": len(endings), "state_matrix_rows": len(states),
                          "original_il_predicate_replays": len(states) * 2, "visible_source_checks": len(evidence_rows),
                          "consumer_cases": len(cases), "missing_sources": len(missing),
                          "installed_line_mismatches": sum(row["installed_exact_encoded_line"] is False for row in evidence_rows)},
              "morning_reachable_paths": morning_paths,
              "burn_button_condition": "unlockedEnding(END_Revenge) && !viewedEnding(END_Revenge)",
              "limitations": ["原IL重放只解释isEndingBurnt的状态读取与布尔跳转；界面显示条件由原populate/Activate静态核对，不称真实Unity组件或像素/E2E验证。",
                              "省略号保持非词汇原样；未执行任何存档业务或解锁/采用操作。",
                              "POSTEND_QuinceBookBurned的31句由并行主任务独立审查；此证据记录选择限制、界面与晨间14次发言。"]}
    save(BUILD / "tests.json", cases)
    consumer = subprocess.run(["pwsh", "-NoProfile", "-File", str(ROOT / "tools/translation/verify-recursive-ui.ps1"),
                               "-TestsPath", str(BUILD / "tests.json")], capture_output=True, text=True, check=True)
    result = json.loads(consumer.stdout.strip().splitlines()[-1])
    assert result == {"actual_recursive_xunity_consumer_passed": True, "count": len(cases)}
    report["consumer_verification"] = {**result, "tests_sha256": sha((BUILD / "tests.json").read_bytes()),
        "verifier_source_sha256": sha((ROOT / "tools/translation/VerifyRecursiveUiRules.cs").read_bytes()),
        "actual_core_sha256": sha((GAME_RESOURCE.parents[1] / "BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll").read_bytes()),
        "definition": "真实XUnity Splitter/ParserResult，逆序首匹配，递归上限64；纯离线，不启动Unity。"}
    save(EVIDENCE, report)
    print(json.dumps(report["summary"], ensure_ascii=False))
    assert not missing


if __name__ == "__main__":
    main()
