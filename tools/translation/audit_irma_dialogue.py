"""提取全部剧情资源中的伊尔玛对白，并生成当前译文的定向消费者用例。"""

import hashlib
import json
from pathlib import Path
import re
import sys

from prepare_dialogue_log_followup import DIALOGUE, ROOT, read, save
from prepare_lead_followup import runtime_source

sys.path.insert(0, str(ROOT / "analysis"))
from analyze import read_text_assets


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {r["source"]: r for r in translations}
    rows, assets = {}, []
    for name, asset_sha, text in read_text_assets(Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/resources.assets").read_bytes()):
        clean = re.sub(r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/',
                       lambda m: m.group() if m.group().startswith('"') else re.sub(r'[^\r\n]', ' ', m.group()), text)
        count = 0
        for match in DIALOGUE.finditer(clean):
            if match["actor"] != "irma":
                continue
            source = json.loads('"' + match["text"] + '"')
            runtime = runtime_source(source)
            count += 1
            entry = (targets.get(runtime) or targets.get(source) or targets.get(source.strip())
                     or targets.get(re.sub(r"\s+", " ", source).strip()))
            if entry is None:
                if re.search("[A-Za-z]", re.sub("<[^>]*>", "", source)):
                    raise ValueError("伊尔玛真实对白缺译文：" + source)
                entry = {"id": "punctuation-" + hashlib.sha256(source.encode()).hexdigest()[:12], "target": source}
            row = rows.setdefault(source, {"id": entry["id"], "source": source, "runtime_source": runtime,
                                           "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                                           "target": entry["target"], "origins": []})
            row["origins"].append({"asset": name, "asset_sha256": asset_sha,
                                   "line": text[:match.start()].count("\n") + 1})
        if count:
            assets.append({"asset": name, "asset_sha256": asset_sha, "occurrences": count})
    rows = list(rows.values())
    cases = []
    for i, row in enumerate(rows):
        cases.extend([
            {"id": "irma-leaf-" + str(i), "source": row["runtime_source"], "target": row["target"], "origins": row["origins"]},
            {"id": "irma-speaker-" + str(i), "source": "<b>Irma:</b> <indent=16%>" + row["runtime_source"],
             "target": "<b>伊尔玛:</b> <indent=16%>" + row["target"], "origins": row["origins"]}])
    related = [r for r in translations if re.search(r"\b(?:Gerta|Biene)\b", r["source"], re.I)
               or r["id"] == "p15096-2e2aaa47cce5"]
    for row in related:
        cases.append({"id": "irma-related-" + row["id"], "source": row["source"], "target": row["target"],
                      "origins": ["translation/sol-full-2026-10-09/translations.json:" + row["id"]]})
    # 用真实通知和昵称原文构造格式压力用例；统一标签不表示这些角色实际说过这些话。
    notice_source = "<b>Ophelia</b> learns about an event.\n"
    notice_target = targets[notice_source]["target"]
    for row in related:
        source = "<b>Irma:</b> <indent=16%>" + row["source"]
        target = "<b>伊尔玛:</b> <indent=16%>" + row["target"]
        cases.append({"id": "irma-related-notice-" + row["id"], "source": notice_source + source,
                      "target": notice_target + target})
    save(ROOT / "runtime/build/irma-review/all.json", rows)
    save(ROOT / "translation/supplemental/irma-review-tests.json", cases)
    save(ROOT / "runtime/evidence/irma-source-audit.json", {"assets": assets, "occurrences": sum(a["occurrences"] for a in assets),
         "unique_dialogues": len(rows), "related_entries": len(related), "consumer_cases": len(cases),
         "dialect_sources": [{"id": r["id"], "source": r["source"], "target": r["target"]} for r in rows
                            if re.search(r"\b(?:Maike|Biene|Aye|Ay|yer|lass|ninnyin')\b", r["source"], re.I)],
         "limits": ["全部资源文本中以irma作为发言者的对白；不宣称其它人物全文已人工审校",
                    "跨昵称的统一发言标签仅检查格式组合，不代表实际剧情",
                    "记录生成和语义审校分开，生成用例不等于消费者验证通过"]})
    print(json.dumps({"assets": len(assets), "unique_dialogues": len(rows), "cases": len(cases)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
