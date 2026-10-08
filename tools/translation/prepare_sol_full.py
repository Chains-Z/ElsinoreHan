"""将既有全量清单分成可追溯的 Sol 翻译任务，不调用模型。"""

import hashlib
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "translation" / "sol-full-2026-10-09"
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "tools" / "translation"))
import analyze
from prepare_pilot import read_dialogues


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-assembly", action="store_true")
    parser.add_argument("--append-short-dialogues", action="store_true")
    args = parser.parse_args()
    if args.append_short_dialogues:
        manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("short_dialogues_appended"):
            raise SystemExit("短对白已追加，拒绝重复生成")
        assets = list(analyze.read_text_assets((analyze.GAME / "resources.assets").read_bytes()))
        names = json.loads((OUTPUT / "character-names.json").read_text(encoding="utf-8"))
        known = {analyze.normalize(row["source"]) for row in manifest["entries"]}
        added = []
        for name, digest, body in sorted(assets, key=lambda row: len(row[2]), reverse=True):
            if not name.startswith("scenes") or name == "scenes_declarations":
                continue
            for row in read_dialogues(body, digest, names):
                source = row["message"]
                key = analyze.normalize(source)
                if key in known or not re.search(r"[A-Za-z]", source):
                    continue
                known.add(key)
                added.append({"id": "s" + str(len(added)).zfill(5) + "-" + row["source_text_sha256"][:12],
                              "source": source, "source_sha256": row["source_text_sha256"],
                              "origins": [row["id"]], "categories": ["dialogue_exact_supplement"],
                              "context": {"scene": row["scene"], "speaker": row["name"], "cues": row["acting_cues"],
                                          "line": row["source_line"], "asset_sha256": digest}})
        for start in range(0, len(added), 200):
            members = added[start:start + 200]
            identifier = f"b{len(manifest['batches']) + 1:04d}"
            for row in members:
                row["batch"] = identifier
            save(OUTPUT / "inputs" / (identifier + ".json"), members)
            manifest["batches"].append({"id": identifier, "count": len(members), "source_characters": sum(len(row["source"]) for row in members)})
            manifest["entries"].extend(members)
        manifest.update({"count": len(manifest["entries"]), "short_dialogues_appended": True, "exact_dialogue_supplement_count": len(added)})
        save(OUTPUT / "manifest.json", manifest)
        print(json.dumps({"added_exact_dialogues": len(added), "total": manifest["count"], "batches": len(manifest["batches"])}))
        return
    if args.append_assembly:
        manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("assembly_appended"):
            raise SystemExit("程序集可见文本已追加，拒绝重复生成")
        classification = json.loads((OUTPUT / "assembly-classification.json").read_text(encoding="utf-8"))
        rows = []
        for item in classification:
            if item["decision"] != "translate":
                continue
            source = item["source"]
            digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
            rows.append({"id": "a" + str(item["index"]).zfill(5) + "-" + digest[:12], "source": source,
                         "source_sha256": digest, "origins": ["assembly_review:" + str(item["index"])],
                         "categories": [item["kind"]], "context": {"type": "实际程序集额外可见文本", "classification_reason": item["reason"]}})
        members, size = [], 0
        def append_batch():
            nonlocal members, size
            if not members:
                return
            identifier = f"b{len(manifest['batches']) + 1:04d}"
            for row in members:
                row["batch"] = identifier
            save(OUTPUT / "inputs" / (identifier + ".json"), members)
            manifest["batches"].append({"id": identifier, "count": len(members), "source_characters": size})
            manifest["entries"].extend(members)
            members, size = [], 0
        for row in rows:
            if members and (len(members) >= 220 or size + len(row["source"]) > 10000):
                append_batch()
            members.append(row)
            size += len(row["source"])
        append_batch()
        manifest.update({"count": len(manifest["entries"]), "assembly_appended": True,
                         "assembly_translate_count": len(rows), "assembly_excluded_count": sum(row["decision"] == "exclude" for row in classification),
                         "assembly_uncertain_count": sum(row["decision"] == "uncertain" for row in classification)})
        save(OUTPUT / "manifest.json", manifest)
        print(json.dumps({"count": manifest["count"], "batches": len(manifest["batches"]), "added_assembly": len(rows)}))
        return
    if (OUTPUT / "manifest.json").exists():
        raise SystemExit("已有冻结任务，拒绝覆盖；新增程序集任务须使用独立目录")
    inventory = json.loads((ROOT / "analysis" / "text_inventory.json").read_text(encoding="utf-8"))
    assets = list(analyze.read_text_assets((analyze.GAME / "resources.assets").read_bytes()))
    names = {}
    for name, _, text in assets:
        if name == "name_mapping":
            names.update(analyze.read_json(text))
    contexts = {}
    for name, digest, body in sorted(assets, key=lambda row: len(row[2]), reverse=True):
        if not name.startswith("scenes") or name == "scenes_declarations":
            continue
        for row in read_dialogues(body, digest, names):
            key = analyze.normalize(row["message"])
            contexts.setdefault(key, {"scene": row["scene"], "speaker": row["name"],
                                      "cues": row["acting_cues"], "line": row["source_line"],
                                      "asset_sha256": digest})
    entries = []
    for index, item in enumerate(inventory):
        source = item["text"]
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        entries.append({"id": "p" + str(index).zfill(5) + "-" + digest[:12], "source": source,
                        "source_sha256": digest, "origins": item["origins"], "categories": item["categories"],
                        "context": contexts.get(analyze.normalize(source), {"type": "资料、界面或未定位对白"})})
    batches, members, size = [], [], 0
    def flush():
        nonlocal members, size
        if not members:
            return
        identifier = f"b{len(batches) + 1:04d}"
        for row in members:
            row["batch"] = identifier
        save(OUTPUT / "inputs" / (identifier + ".json"), members)
        batches.append({"id": identifier, "count": len(members), "source_characters": size})
        members, size = [], 0
    for row in entries:
        if members and (len(members) >= 220 or size + len(row["source"]) > 10000):
            flush()
        members.append(row)
        size += len(row["source"])
    flush()
    save(OUTPUT / "manifest.json", {"model": "gpt-6.1-sol", "count": len(entries), "batches": batches,
                                    "inventory_sha256": hashlib.sha256((ROOT / "analysis" / "text_inventory.json").read_bytes()).hexdigest(),
                                    "entries": entries, "limitations": ["静态候选含未启用文本，不能代表游戏内全分支验收", "同句不同语境暂共用译文，疑难句留待游玩修订"]})
    glossary = json.loads((ROOT / "translation" / "trial-2026-10-09" / "glossary.json").read_text(encoding="utf-8"))
    save(OUTPUT / "glossary.json", glossary)
    save(OUTPUT / "character-names.json", names)
    save(OUTPUT / "output-schema.json", {"type": "object", "additionalProperties": False,
        "properties": {"translations": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"id": {"type": "string"}, "target": {"type": "string"}}, "required": ["id", "target"]}}},
        "required": ["translations"]})
    print(json.dumps({"count": len(entries), "batches": len(batches), "source_characters": sum(len(row["source"]) for row in entries)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
