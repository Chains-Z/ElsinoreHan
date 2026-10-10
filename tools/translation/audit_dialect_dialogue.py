"""筛查真实剧情资源的方言/口语，并为人工审校范围生成离线消费者用例。"""

import collections
import hashlib
import json
import re
from pathlib import Path
import sys

from prepare_dialogue_log_followup import (
    AUDIT, DIALOGUE, GAME_RESOURCE, ROOT, SCENE, SPECIAL_NAMES,
    dialogue_source, read, save, short_name,
)

sys.path.insert(0, str(ROOT / "analysis"))
from analyze import read_text_assets


# 标记只用于选择人工审校候选；不把同形标准用词或方言写法自动判为错译。
MARKERS = re.compile(
    r"\b(?:ain't|aint|yer|yers|yeh|ye|yep|aye|ay|nay|lass|lad|lads|laddie|lassie|"
    r"y'all|yall|youse|ya|nah|naw|gonna|wanna|gotta|oughta|outta|sorta|kinda|dunno|"
    r"lemme|gimme|c'mon|cmon|feh|bah|eh|huh|oy|oi|innit|reckon|maike|biene|ninnyin|"
    r"ja|nein|fräulein|mein|gawd|blimey|bloody|bugger|bollocks|git|chap|fella|fellers|"
    r"fellas|bairn|wee|bonnie|bonny|dinna|ken|ta|wos|wot|thas|jus|dunnah|dunna|"
    r"dunneh|dunnow|doncha|dontcha|atcha|whatcha|whaddya|wuz|sez|cor|tsk|tut|"
    r"faugh|pah|harr|har|arrr|argh|guh|och|ach|bloke|rotter|botheration|"
    r"fiddlesticks|golly|gee|shucks|varmint|fer)\b|"
    r"\b\w{2,}in'(?=[\s,.!?;—-]|$)|\bol'(?=[\s,.!?;—-]|$)|"
    r"\b(?:y|th|t|m|d|cap|more|better|fer)'[A-Za-z]+\b|"
    r"(?<!\w)'(?:em|im|er|ere|cause|tis|twas|til|bout|round|ave|ope|ello|is|e|n|feely)\b",
    re.I,
)
FULL_REVIEW_ACTORS = {"marcellus", "grace", "guard", "guard2", "brigand", "brigand2",
                      "pirate", "pirate2", "villager", "villager2"}


def extract_rows(translations):
    """提取全部TextAsset的角色对白；上下文保留原行号与场景，不能当顺序剧情执行。"""
    targets = {r["source"]: r for r in translations}
    rows, assets = {}, []
    for name, asset_sha, text in read_text_assets(GAME_RESOURCE.read_bytes()):
        clean = re.sub(r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/',
                       lambda m: m.group() if m.group().startswith('"') else re.sub(r'[^\r\n]', ' ', m.group()), text)
        matches, scenes = list(DIALOGUE.finditer(clean)), list(SCENE.finditer(clean))
        scene_index = -1
        for index, match in enumerate(matches):
            while scene_index + 1 < len(scenes) and scenes[scene_index + 1].start() < match.start():
                scene_index += 1
            source = json.loads('"' + match["text"] + '"')
            actor = match["actor"]
            runtime = dialogue_source(actor, source)
            entry = (targets.get(runtime) or targets.get(source) or targets.get(source.strip())
                     or targets.get(re.sub(r"\s+", " ", source).strip()))
            row = rows.setdefault((actor, source), {
                "actor": actor, "source": source, "runtime_source": runtime,
                "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "id": entry["id"] if entry else None, "target": entry["target"] if entry else None,
                "origins": [], "context": [], "markers": sorted({m.group() for m in MARKERS.finditer(source)}),
            })
            row["origins"].append({"asset": name, "asset_sha256": asset_sha,
                                    "scene": scenes[scene_index][1] if scene_index >= 0 else None,
                                    "line": text[:match.start()].count("\n") + 1})
            if not row["context"]:
                row["context"] = [{"actor": m["actor"], "source": json.loads('"' + m["text"] + '"')}
                                  for m in matches[max(0, index - 2):index + 3]]
        if matches:
            assets.append({"asset": name, "asset_sha256": asset_sha, "occurrences": len(matches)})
    return list(rows.values()), assets


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {r["source"]: r for r in translations}
    rows, assets = extract_rows(translations)
    selected = [r for r in rows if r["actor"] != "irma"
                and (r["actor"] in FULL_REVIEW_ACTORS or r["markers"])]
    resource = read(AUDIT / "resource-strings.json")
    mapping = {r["origin"]["field"]: r["source"] for r in resource
               if r["origin"].get("asset") == "name_mapping"}
    cases = []
    notice_source = "<b>Ophelia</b> learns about an event.\n"
    notice_target = targets[notice_source]["target"]
    for index, row in enumerate(selected):
        if row["target"] is None:
            if re.search("[A-Za-z]", re.sub("<[^>]*>", "", row["source"])):
                raise ValueError("定向审校对白没有对应译文：" + row["source"])
            row["target"] = row["runtime_source"]
        name = short_name(row["actor"], mapping)
        target_name = SPECIAL_NAMES.get(name) or (targets[name]["target"] if name != "???" else "???")
        speaker_source = "<b>" + name + ":</b> <indent=16%>" + row["runtime_source"]
        speaker_target = "<b>" + target_name + ":</b> <indent=16%>" + row["target"]
        for kind, source, target in (
            ("leaf", row["runtime_source"], row["target"]),
            ("speaker", speaker_source, speaker_target),
            ("notice-before", notice_source + speaker_source, notice_target + speaker_target),
            ("notice-after", speaker_source + "</indent>\n" + notice_source,
             speaker_target + "</indent>\n" + notice_target),
        ):
            cases.append({"id": "dialect-" + str(index) + "-" + kind,
                          "source": source, "target": target, "origins": row["origins"]})
    save(ROOT / "runtime/build/dialect-review/all.json", rows)
    save(ROOT / "runtime/build/dialect-review/selected.json", selected)
    save(ROOT / "translation/supplemental/dialect-review-tests.json", cases)
    report = {"assets": assets, "resource_occurrences": sum(a["occurrences"] for a in assets),
              "unique_actor_sources_screened": len(rows), "resource_actors": len({r["actor"] for r in rows}),
              "marked_non_irma_rows": sum(bool(r["markers"]) and r["actor"] != "irma" for r in rows),
              "review_selection": len(selected), "selected_by_actor": dict(collections.Counter(r["actor"] for r in selected)),
              "full_review_actors": sorted(FULL_REVIEW_ACTORS), "consumer_cases": len(cases),
              "limits": ["词形筛选不等于判断错误，也不代表全部人物全文经过人工审校",
                         "相邻资源上下文可能含互斥分支，不能冒充实际完整游玩",
                         "通知前后组合是消费路径检查，不代表具体剧情出现该组合"]}
    save(ROOT / "runtime/evidence/dialect-source-audit.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "assets"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
