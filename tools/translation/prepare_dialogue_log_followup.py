"""核查全部真实脚本对白与日志短名，生成定向规则和资源组合夹具。"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from analyze import read_text_assets, remove_comments
from export_sol_full import encode
from prepare_lead_followup import runtime_source

OUT = ROOT / "translation/supplemental"
AUDIT = ROOT / "analysis/ui-audit"
FULL = ROOT / "translation/sol-full-2026-10-09"
GAME_RESOURCE = Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/resources.assets")
DIALOGUE = re.compile(r'^\s*(?P<actor>\w+)\s*:\s*(?:(?:\[[^\]\r\n]*\]|\{[^}\r\n]*\})\s*)*"(?P<text>(?:\\.|[^"\\])*)"', re.M)
SCENE = re.compile(r'^\{([^\r\n{}]+)\}\s*$', re.M)
SPECIAL_NAMES = {"Ghost": "幽灵", "Figure": "戴兜帽的人", "Woman": "老妇人", "Grace": "格蕾丝"}


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def short_name(actor, mapping):
    """精确复现已审FormatShortCharacterName，不根据称谓语义猜短名。"""
    if actor == "rosencrantz":
        return "Rosie"
    if actor == "guildenstern":
        return "Guilda"
    return mapping[actor].split(" ")[1] if " " in mapping[actor] else mapping[actor]


def dialogue_source(actor, source):
    """编译时九步替换，幽灵对白在随后pass整体外套斜体。"""
    text = runtime_source(source)
    return "<i>" + text + "</i>" if actor == "ghost" else text


def source_rows():
    """解析全部三个真实scenes资产的发言行，不把舞台参数或逻辑字符串当对白。"""
    rows, assets = [], []
    for name, asset_hash, text in read_text_assets(GAME_RESOURCE.read_bytes()):
        if name != "scenes":
            continue
        assets.append({"asset": name, "sha256": asset_hash, "length": len(text)})
        # 用等长空白替换注释，保持原行号和字符位置可追溯。
        clean = re.sub(r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/',
                       lambda m: m.group() if m.group().startswith('"') else re.sub(r'[^\r\n]', ' ', m.group()), text)
        scenes = list(SCENE.finditer(clean))
        scene_index = -1
        for match in DIALOGUE.finditer(clean):
            while scene_index + 1 < len(scenes) and scenes[scene_index + 1].start() < match.start():
                scene_index += 1
            source = json.loads('"' + match["text"] + '"')
            rows.append({"actor": match["actor"], "source": source,
                         "source_sha256": digest(source), "runtime_source": dialogue_source(match["actor"], source),
                         "origin": {"asset": name, "asset_sha256": asset_hash,
                                    "scene": scenes[scene_index][1] if scene_index >= 0 else None,
                                    "line": text[:match.start()].count("\n") + 1}})
    return rows, assets


def make_rules(mapping, exported):
    """只补旧日志四种结构中的真实短名，保留旧规则以便回溯比较。"""
    names = sorted(set(mapping.values()), key=lambda s: (-len(s), s))
    short = sorted({short_name(k, mapping) for k in mapping}, key=lambda s: (-len(s), s))
    missing = sorted(set(short) - set(names) - {"Rosie", "Guilda"})
    rules = []
    wanted = {"ui-rule-log-header", "ui-rule-log-speaker-boundary", "ui-rule-log-italic-boundary", "ui-rule-log-speaker"}
    for old in exported:
        if old["id"] not in wanted:
            continue
        # 原真实姓名集合出现多次，每处都添加完整短名集合；不改结果通知的全名语法。
        pattern = old["pattern"]
        insertion = "|".join(re.escape(s) for s in missing) + "|"
        marker = "(?:Lady\\ Guildenstern|"
        if marker not in pattern:
            raise ValueError("旧日志姓名集合结构变化，请重新审核")
        pattern = pattern.replace(marker, "(?:" + insertion + "Lady\\ Guildenstern|")
        rules.append({"id": old["id"] + "-shortnames-followup", "priority": old.get("priority", 0) + 1,
                      "pattern": pattern, "replacement": old["replacement"],
                      "origins": ["analysis/ui-audit/dialogue-log-followup-il.json", "resources.assets:name_mapping"],
                      "note": "真实FormatShortCharacterName第二词及Rosie/Guilda特判；限定日志speaker结构；正文仍必须完整递归消费"})
    for name, target in SPECIAL_NAMES.items():
        rules.append({"id": "ui-rule-log-shortname-label-" + name.lower(), "priority": 12,
                      "pattern": r"^(?<open_i><b>)" + re.escape(name) + r"(?<label_i>:</b> <indent=16%>)(?<body>[\s\S]+?)(?<close_i></indent>)?\z$",
                      "replacement": "${open_i}" + target + "${label_i}${body}${close_i}",
                      "origins": ["analysis/ui-audit/dialogue-log-followup-il.json", "resources.assets:name_mapping"],
                      "note": "仅翻译真实发言短名标签，不将Figure/Woman/Grace等单词全局替换"})
    # 一次拆八个完整发言块，长记录按八块推进，避免逐块形成过深递归。
    name_union = "(?:" + "|".join(re.escape(s) for s in sorted(set(short), key=lambda s: (-len(s), s))) + ")"
    block = "<b>" + name_union + r":</b> <indent=16%>[\s\S]+?</indent>"
    chunks = ["(?<part" + str(i) + ">" + block + ")(?<boundary" + str(i) + r"_i>\n)" for i in range(1, 9)]
    rules.append({"id":"ui-rule-log-speaker-eight-blocks","priority":55,
                  "pattern":"^" + "".join(chunks) + "(?<rest><b>" + name_union + r":</b> <indent=16%>[\s\S]+)\z$",
                  "replacement":"".join("${part" + str(i) + "}${boundary" + str(i) + "_i}" for i in range(1,9)) + "${rest}",
                  "origins":["analysis/ui-audit/dialogue-log-followup-il.json", "resources.assets:name_mapping"],
                  "note":"按真实完整speaker/indent块一次八块；各part独立递归消费，未知正文仍拒绝；不提高64上限、不按任意LF切单句"})
    return rules, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-directory", type=Path, help="生成临时合并词表和规则供真实消费者比较，不改正式导出")
    args = parser.parse_args()
    translations = read(FULL / "translations.json")
    by_source = {r["source"]: r for r in translations}
    original_by_source = {r["source"]: r for r in translations if not r["id"].startswith("ui-dialogue-runtime-")}
    resource = read(AUDIT / "resource-strings.json")
    mapping = {r["origin"]["field"]: r["source"] for r in resource if r["origin"].get("asset") == "name_mapping"}
    rows, assets = source_rows()
    aliases = {}
    for row in rows:
        if row["actor"] not in mapping:
            raise ValueError("实际发言者不在NameMap：" + row["actor"])
        raw = row["source"]
        core = runtime_source(raw)
        frozen = original_by_source.get(raw) or original_by_source.get(raw.strip()) or original_by_source.get(re.sub(r"\s+", " ", raw).strip())
        if frozen is None:
            if re.search("[A-Za-z]", re.sub("<[^>]*>", "", raw)):
                raise ValueError("真实对白缺冻结译文：" + raw[:120])
            row["target"] = row["runtime_source"]
        else:
            runtime_exact = by_source.get(row["runtime_source"]) or by_source.get(row["runtime_source"].strip())
            row["target"] = runtime_exact["target"] if runtime_exact else ("<i>" + frozen["target"] + "</i>" if row["actor"] == "ghost" else frozen["target"])
            should_retain_alias = core not in by_source or by_source[core]["id"].startswith("ui-dialogue-runtime-")
            if should_retain_alias and core.strip() != frozen["source"].strip() and re.search("[A-Za-z]", core):
                if core in by_source and by_source[core]["target"] != frozen["target"]:
                    raise ValueError("现有对白运行别名译文与冻结正文不一致")
                aliases.setdefault(core, {"id": "ui-dialogue-runtime-" + digest(core)[:16], "source": core,
                    "source_sha256": digest(core), "target": frozen["target"], "existing_id": frozen["id"],
                    "existing_source": frozen["source"], "existing_source_sha256": digest(frozen["source"]),
                    "existing_target_sha256": digest(frozen["target"]),
                    "origins": [row["origin"], "analysis/ui-audit/dialogue-log-followup-il.json"],
                    "provenance": "真实对白编译九步破折号或资源空白变体，逐字复用冻结译文，不重翻正文"})
        row["short_name"] = short_name(row["actor"], mapping)
        row["short_target"] = SPECIAL_NAMES.get(row["short_name"]) or by_source[row["short_name"]]["target"] if row["short_name"] != "???" else "???"
    exported = read(FULL / "dynamic-rules.json")
    rules, missing = make_rules(mapping, exported)
    italic_sources = sorted({r["runtime_source"].rstrip() for r in rows if r["runtime_source"].startswith("<i>")}, key=lambda s: (-len(s),s))
    rules.append({"id":"ui-rule-log-italic-dialogue-continuation","priority":54,
                  "pattern":"^(?<first>(?:" + "|".join(re.escape(s) for s in italic_sources) + r"))(?<newline_i>[ \t]*\n)(?<rest>[\s\S]+)\z$",
                  "replacement":"${first}${newline_i}${rest}",
                  "origins":["analysis/ui-audit/dialogue-log-followup-il.json", "scenes:真实斜体对白完整源"],
                  "note":"优先消费完整斜体唱词/幽灵对白的同人续行，避免通用舞台斜体边界抢先跨句；只接受已审完整对白原子"})
    # 新变体、真实开头空格和纯标点首句仅增量进入续行白名单。
    extra_candidates = {r["source"] for r in aliases.values()} | {"<i>" + r["source"] + "</i>" for r in aliases.values()}
    extra_candidates |= {r["runtime_source"].rstrip() for r in rows
                         if r["runtime_source"] != r["runtime_source"].lstrip()
                         or not re.search("[A-Za-z]", re.sub("<[^>]*>", "", r["runtime_source"]))}
    if extra_candidates:
        candidates = sorted(extra_candidates, key=lambda s: (-len(s), s))
        rules.append({"id": "ui-rule-log-runtime-alias-continuation", "priority": 1,
                      "pattern": "^(?<first>(?:" + "|".join(re.escape(s) for s in candidates) + r"))(?<newline_i>[ \t]*\n)(?<rest>[\s\S]+)\z$",
                      "replacement": "${first}${newline_i}${rest}",
                      "origins": ["analysis/ui-audit/dialogue-log-followup-il.json", "translation/supplemental/dialogue-log-runtime-aliases.json"],
                      "note": "只消费新增已审破折号运行变体的真实连续发言，不泛化任意英文换行"})
    cases = []
    seen = set()
    def add(identifier, source, target, origins, category):
        if (source, target) in seen:
            return
        seen.add((source, target))
        cases.append({"id": identifier, "source": source, "target": target,
                      "source_sha256": digest(source), "target_sha256": digest(target) if target is not None else None,
                      "origins": origins, "category": category,
                      "verification_level": "实际资源及真实日志格式组件组合，不代表相应剧情路径已游玩"})
    def speaker(row, target=False):
        return "<b>" + row["short_target" if target else "short_name"] + ":</b> <indent=16%>" + row["target" if target else "runtime_source"]
    for i, row in enumerate(rows):
        add("dialogue-log-single-" + str(i), speaker(row), speaker(row, True), [row["origin"]], "single")
        if i and rows[i-1]["origin"]["asset_sha256"] == row["origin"]["asset_sha256"] and rows[i-1]["origin"]["scene"] == row["origin"]["scene"]:
            previous = rows[i-1]
            same = previous["actor"] == row["actor"]
            source = speaker(previous) + ("\n" + row["runtime_source"] if same else "</indent>\n" + speaker(row))
            padding = previous["runtime_source"][len(previous["runtime_source"].rstrip()):]
            target = speaker(previous, True) + (padding + "\n" + row["target"] if same else "</indent>\n" + speaker(row, True))
            add("dialogue-log-pair-" + str(i), source, target, [previous["origin"],row["origin"]], "same_speaker" if same else "different_speaker")
    first = rows[0]
    for short in sorted(set(short_name(k, mapping) for k in mapping)):
        target = SPECIAL_NAMES.get(short) or (by_source[short]["target"] if short != "???" else "???")
        add("dialogue-log-shortname-" + short, "<b>" + short + ":</b> <indent=16%>Dinner is served.",
            "<b>" + target + ":</b> <indent=16%>" + by_source["Dinner is served."]["target"], ["resources.assets:name_mapping"], "all_shortnames")
    for unknown in ("UnknownActor", "names.actors.claudius"):
        add("dialogue-log-reject-name-" + unknown, "<b>" + unknown + ":</b> <indent=16%>Dinner is served.", None, ["未知发言者拒绝"], "negative")
    add("dialogue-log-reject-body", "<b>Claudius:</b> <indent=16%>Unknown internal dialogue marker.", None, ["未知正文拒绝"], "negative")
    valid_block="<b>Claudius:</b> <indent=16%>Dinner is served.</indent>\n"
    for identifier, source in (
        ("dialogue-log-reject-eighth-body",valid_block*7+"<b>Claudius:</b> <indent=16%>Unknown internal dialogue marker.</indent>\n"+valid_block[:-10]),
        ("dialogue-log-reject-rest-body",valid_block*8+"<b>Claudius:</b> <indent=16%>Unknown internal dialogue marker."),
        ("dialogue-log-reject-rest-name",valid_block*8+"<b>UnknownActor:</b> <indent=16%>Dinner is served."),
        ("dialogue-log-reject-continuation", "<b>Claudius:</b> <indent=16%>Dinner is served.\nUnknown internal dialogue marker.")):
        add(identifier,source,None,["真实八块/续行结构中未知项拒绝，不换其它规则兜底"],"negative")
    groups = {}
    for row in rows:
        key = (row["origin"]["asset_sha256"],row["origin"]["scene"])
        groups.setdefault(key, []).append(row)
    longest = max(groups.values(),key=len)
    def group_content(group, target=False):
        output = ""
        previous = None
        for row in group:
            if previous is not None and previous["actor"] == row["actor"]:
                padding = previous["runtime_source"][len(previous["runtime_source"].rstrip()):] if target else ""
                output += padding + "\n" + row["target" if target else "runtime_source"]
            else:
                output += ("</indent>\n" if previous else "") + speaker(row,target)
            previous=row
        return output
    # 全场景静态顺序含条件的互斥分支，是深度压力夹具，不宣称实际可发生路径。
    add("dialogue-log-longest-scene-stress", group_content(longest),group_content(longest,True),
        [longest[0]["origin"],{"warning":"按资源顺序串联包括互斥分支，仅检查递归深度，不代表实际剧情"}], "depth_stress")
    for key, group in groups.items():
        add("dialogue-log-scene-stress-" + digest(str(key))[:12],group_content(group),group_content(group,True),
            [group[0]["origin"],{"warning":"静态顺序含互斥分支，仅为真实格式压力夹具"}],"depth_stress")
    for needle, take in (("Dinner is served.",16),("There may be more to this than mere lovesickness.",4)):
        start=next(i for i,r in enumerate(rows) if r["source"]==needle)
        group=rows[start:start+take]
        # 晚餐截图没有雷欧提斯支线三句；只使用图片实际出现且可追溯的发言。
        if needle == "Dinner is served.":
            group=[r for i,r in enumerate(group) if i not in (4,5,6)]
        add("dialogue-log-screenshot-" + ("dinner" if needle=="Dinner is served." else "court"),
            group_content(group),group_content(group,True),[r["origin"] for r in group],"screenshot")
    depth_cases = [r for r in cases if r["category"] == "depth_stress"]
    cases = [r for r in cases if r["category"] != "depth_stress"]
    save(OUT / "dialogue-log-followup-rules.json", rules)
    save(OUT / "dialogue-log-runtime-aliases.json", list(aliases.values()))
    save(OUT / "dialogue-log-followup-tests.json", cases)
    save(OUT / "dialogue-log-depth-tests.json", depth_cases)
    save(OUT / "dialogue-log-representative-tests.json", [r for r in cases if r["category"] in {"all_shortnames","negative","screenshot"}])
    save(AUDIT / "dialogue-log-source-audit.json", {"schema_version":1,"source_assets":assets,
        "parsed_dialogue_occurrences":len(rows),"unique_runtime_dialogues":len({r["runtime_source"] for r in rows}),
        "short_names":{actor:short_name(actor,mapping) for actor in mapping},"missing_shortnames_in_old_rules":missing,
        "runtime_aliases":len(aliases),"case_count":len(cases),"longest_source":max(len(r["runtime_source"]) for r in rows),
        "longest_same_actor_run":max(len(list(g)) for _,g in itertools.groupby(rows,key=lambda r:(r["origin"]["asset_sha256"],r["origin"]["scene"],r["actor"]))),
        "longest_scene_stress": {"origin":longest[0]["origin"],"dialogue_count":len(longest),"warning":"含互斥分支的静态资源压力夹具，不代表实际剧情"},
        "parse_contract":"以全部真实actor冒号引号发言行提取，注释置等长空白，保留行号；舞台参数与逻辑字符串不作为对白",
        "dialogues":rows})
    if args.offline_directory:
        directory=args.offline_directory
        combined_translations=translations+[r for r in aliases.values() if r["source"] not in by_source]
        new_ids={r["id"] for r in rules}
        baseline=[r for r in exported if r["id"] not in new_ids]
        rendered=[]
        for rule in rules:
            rendered.append({**rule,"kind":"recursive_ui_splitter","encoded_line":encode('sr:"'+rule['pattern']+'"')+'='+encode('"'+rule['replacement']+'"')})
        combined=sorted(baseline+rendered,key=lambda r:r.get("priority",0))
        save(directory/"combined-translations.json",combined_translations)
        save(directory/"combined-rules.json",combined)
        save(directory/"baseline-rules.json",baseline)
    print(json.dumps({"parsed_dialogues":len(rows),"cases":len(cases),"rules":len(rules),"runtime_aliases":len(aliases),"longest_scene_entries":len(longest)},ensure_ascii=False))


if __name__ == "__main__":
    main()
