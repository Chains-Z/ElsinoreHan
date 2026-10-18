"""复核谢幕全部分支的真实资源、编译源与审校记录，导出对照稿及消费者夹具。"""

import json
import re

from export_sol_full import apply_supplemental
from prepare_shakespeare_names_followup import reading_names
from prepare_ending_style_followup import reading_style
from prepare_dialogue_log_followup import (
    DIALOGUE, GAME_RESOURCE, ROOT, SCENE, dialogue_source, digest, read,
    read_text_assets, save, short_name, source_rows,
)


DIRECTORY = ROOT / "translation/supplemental"
DESTINATION = ROOT / "docs/dev-tasks/localization/curtain-call-review-2026-10-18"
ENDING_IDS = {
    "END_CurtainCall_Resignation": "END_Resignation",
    "END_CurtainCall_Queen": "END_Queen",
    "END_CurtainCall_Pirate": "END_Pirate",
    "END_CurtainCall_Othello": "END_Othello",
    "END_CurtainCall_OpheliaLeaves": "END_SentAway",
    "END_CurtainCall_RosAndGuil": "END_RosAndGuil",
    "END_CurtainCall_Exile": "END_Exile",
    "END_CurtainCall_Insanity": "END_Delusion",
    "END_CurtainCall_EveryoneSurvives": "END_Survival",
    "END_CurtainCall_Hamlet": "END_HamletMarriage",
    "END_CurtainCall_FortinbrasRules": "END_FortinbrasPeaceful",
}


def display(value):
    """逐标签展示强调，兼容幽灵外层斜体中的嵌套粗体。"""
    return re.sub(r"</(?:i|b)>", "」", re.sub(r"<(?:i|b)>", "「", value))


def main():
    review = read(DIRECTORY / "curtain-call-review.json")
    for scene in review["scenes"]:
        scene["paragraphs"] = reading_style(reading_names(scene["paragraphs"]))
    corrections = read(DIRECTORY / "curtain-call-corrections.json")
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row for row in translations}
    changes = {row["source"]: row for row in corrections}
    # 复用导出器的哈希、来源、准确旧值和标记校验；审查预期来自审定清单，不从输出生成。
    previous = [{"id": row["original_id"], "source": row["source"],
                 "target": row["previous_target"]} for row in corrections]
    checked = apply_supplemental(previous, corrections)
    assert len(checked) == len(changes) == review["changed_dictionary_sources"] == 17
    followups = {entry["source"]: entry for entry in read(DIRECTORY / "ending-style-corrections.json")}
    for row in checked:
        assert targets[row["source"]]["id"] == row["id"]
        if row["source"] in followups:
            assert followups[row["source"]]["previous_target"] == row["target"]
            row["target"] = followups[row["source"]]["target"]
        assert targets[row["source"]]["target"] == row["target"]

    actual, _ = source_rows()
    scenes = {scene["scene"]: scene for scene in review["scenes"]}
    actual = [row for row in actual if row["origin"]["scene"] in scenes]
    reviewed = [row for scene in review["scenes"] for row in scene["paragraphs"]]
    assert len(actual) == len(reviewed) == review["reviewed_occurrences"] == 449
    assert len({row["runtime_source"] for row in actual}) == review["unique_runtime_sources"] == 418
    for scene in review["scenes"]:
        fresh = [row for row in actual if row["origin"]["scene"] == scene["scene"]]
        assert len(fresh) == len(scene["paragraphs"])
        for raw, row in zip(fresh, scene["paragraphs"]):
            assert raw["origin"]["asset_sha256"] == review["asset_sha256"]
            assert raw["source"] == row["source"] and raw["actor"] == row["actor"]
            assert raw["runtime_source"] == row["runtime_source"]
            assert raw["source_sha256"] == row["source_sha256"] == digest(row["source"])
            assert digest(row["runtime_source"]) == row["runtime_source_sha256"]
            assert raw["origin"]["line"] == row["line"]

    assembly = {row["source"]: row for row in read(ROOT / "analysis/ui-audit/assembly-strings.json")}
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    cases, regression, source_owners = [], [], []
    notice = "<b>Ophelia</b> learns about an event.\n"
    for index, row in enumerate(reviewed):
        origin = {"asset": "scenes", "asset_sha256": review["asset_sha256"],
                  "line": row["line"], "actor": row["actor"]}
        source, target = row["runtime_source"], row["target"]
        assert source in assembly
        assert assembly[source]["source_sha256"] == digest(source)
        source_owners.append({"source_sha256": digest(source), "actor": row["actor"],
                              "line": row["line"], "usages": assembly[source]["usages"]})
        for kind, text, expected, identifier in (
            ("runtime", source, target, row["runtime_id"]),
            ("resource", row["source"], row["resource_target"], row["id"]),
        ):
            if kind == "resource" and text == source:
                assert expected == target
                continue
            if identifier is None:
                assert row["source"] == "..." and expected == text
            else:
                assert targets[text]["id"] == identifier and targets[text]["target"] == expected
            case = {"id": f"curtain-{index}-{kind}", "source": text,
                    "target": expected, "origins": [origin]}
            cases.append(case)
            if text in changes:
                regression.append(case)
        if source not in changes:
            continue
        cases.append({"id": f"curtain-{index}-dialogue-box", "source": "<line-height=90%>" + source,
                      "target": "<line-height=90%>" + target, "origins": [origin]})
        name = short_name(row["actor"], mapping)
        translated_name = {"Ghost": "幽灵", "Figure": "戴兜帽的人"}.get(name)
        if translated_name is None:
            translated_name = targets[name]["target"]
        speaker = "<b>" + name + ":</b> <indent=16%>" + source
        speaker_target = "<b>" + translated_name + ":</b> <indent=16%>" + target
        for kind, text, expected in (
            ("speaker", speaker, speaker_target),
            ("notice-before", notice + speaker, targets[notice]["target"] + speaker_target),
            ("notice-after", speaker + "</indent>\n" + notice,
             speaker_target + "</indent>\n" + targets[notice]["target"]),
        ):
            cases.append({"id": f"curtain-{index}-{kind}", "source": text,
                          "target": expected, "origins": [origin]})

    assets = [(name, sha, text) for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())
              if name == "endings" or (name == "scenes" and "{END_CurtainCall_GenericSetup}" in text)]
    assert len(assets) == 2
    _, metadata_sha, metadata_text = next(row for row in assets if row[0] == "endings")
    metadata = {row["id"]: row for row in json.loads(metadata_text)["endings"] if row["inbook"]}
    assert set(ENDING_IDS.values()) == set(metadata) and len(metadata) == 11
    _, asset_sha, text = next(row for row in assets if row[0] == "scenes")
    assert asset_sha == review["asset_sha256"]
    markers = list(SCENE.finditer(text))
    blocks = {marker[1]: text[marker.end():markers[index + 1].start() if index + 1 < len(markers) else len(text)]
              for index, marker in enumerate(markers) if marker[1] in scenes}
    reading = ["进入结局前的谢幕：完整中英对照", "",
               "共11个结局分支，加共用开场和收尾；449段发言。不同分支不会在一次游玩中全部播放。",
               "中文在上，英文在下；「」提示原文斜体或粗体；保留条件标记供分支核对。",
               "所有内容按真实脚本列出，包含只在条件满足时播放的发言。", ""]
    for scene in review["scenes"]:
        if scene["scene"] in ENDING_IDS:
            meta = metadata[ENDING_IDS[scene["scene"]]]
            title = "舍弃" + targets[meta["sacrifice-what"]]["target"] + "，换取" + targets[meta["sacrifice-for"]]["target"]
        else:
            title = "谢幕共用开场" if scene["scene"] == "END_CurtainCall_GenericSetup" else "谢幕共用收尾"
        reading.extend([title, scene["scene"], "=" * 40, ""])
        iterator = iter(scene["paragraphs"])
        count = 0
        for line in blocks[scene["scene"]].splitlines():
            match = DIALOGUE.match(line)
            if match:
                row = next(iterator)
                assert json.loads('"' + match["text"] + '"') == row["source"]
                assert dialogue_source(match["actor"], row["source"]) == row["runtime_source"]
                name = mapping[row["actor"]]
                translated_name = {"ghost": "幽灵"}.get(row["actor"]) or targets[name]["target"]
                reading.extend([translated_name + "：" + display(row["target"]),
                                name + ": " + display(row["runtime_source"]), ""])
                count += 1
            elif re.match(r"\s*(?:if |elif |else:|endif)", line):
                reading.extend(["【条件：" + line.strip() + "】", ""])
            elif re.match(r'\s*call "', line):
                reading.extend(["【插入共用段落：" + line.strip() + "】", ""])
            elif 'ForceGameOver("Continue?")' in line:
                reading.extend(["【进入所选结局】", ""])
        assert count == len(scene["paragraphs"])

    destination = DESTINATION / "curtain-call-texts-zh-CN.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(reading), encoding="utf-8", newline="\n")
    save(DIRECTORY / "curtain-call-tests.json", cases)
    save(ROOT / "runtime/build/curtain-call-review/regression-tests.json", regression)
    save(ROOT / "runtime/build/curtain-call-review/source-owners.json", source_owners)
    save(ROOT / "runtime/build/curtain-call-review/source-audit.json", {
        "source_asset_sha256": review["asset_sha256"], "metadata_sha256": metadata_sha,
        "scene_counts": {
            scene["scene"]: len(scene["paragraphs"]) for scene in review["scenes"]},
        "reviewed_occurrences": len(reviewed), "unique_runtime_sources": 418,
        "corrected_occurrences": review["corrected_occurrences"],
        "changed_dictionary_sources": len(changes), "consumer_cases": len(cases),
        "changed_source_regression_cases": len(regression),
        "all_runtime_sources_found_in_assembly": True,
        "reading_copy": str(destination.relative_to(ROOT)),
    })
    print(f"449段谢幕、418条实际源已核对；生成{len(cases)}项真实消费者及完整中英对照稿")


if __name__ == "__main__":
    main()
