"""从真实游戏探针补齐资源粗提取漏掉的短界面标签，不生成假源文。"""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "translation" / "sol-full-2026-10-09"


def main():
    manifest = json.loads((DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("runtime_ui_appended"):
        raise SystemExit("运行UI已追加，拒绝重复生成")
    evidence = max((ROOT / "runtime" / "evidence" / "headless").iterdir(), key=lambda path: path.stat().st_mtime)
    report = evidence / "original-menu-texts.txt"
    normalized = lambda text: re.sub(r"\s+", " ", text).strip()
    known = {normalized(row["source"]) for row in manifest["entries"]}
    placeholders = ("Lorem ipsum", "I'm some text that's talking", "I am a description of the hearsay", "Some Button", "Ver. 0.0.0")
    rows = []
    object_name = ""
    for line in report.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("OBJECT="):
            object_name = line[7:]
        if not line.startswith("TEXT="):
            continue
        source = line[5:].replace("\\n", "\n")
        if not source.strip() or not re.search(r"[A-Za-z]", source) or re.search(r"[\u3400-\u9fff]", source):
            continue
        if source.startswith(placeholders) or normalized(source) in known:
            continue
        if object_name.startswith(("LocationText", "TimeText")) or source == "Show Buttons":
            continue
        known.add(normalized(source))
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        rows.append({"id": "u" + str(len(rows)).zfill(5) + "-" + digest[:12], "source": source,
                     "source_sha256": digest, "origins": [str(report.relative_to(ROOT))], "categories": ["runtime_ui"],
                     "context": {"type": "游戏真实TMP界面组件；静态资源粗提取遗漏的短标签", "object": object_name}})
    if rows:
        batch = f"b{len(manifest['batches']) + 1:04d}"
        for row in rows:
            row["batch"] = batch
        (DIRECTORY / "inputs" / (batch + ".json")).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["batches"].append({"id": batch, "count": len(rows), "source_characters": sum(len(row["source"]) for row in rows)})
        manifest["entries"].extend(rows)
    manifest.update({"count": len(manifest["entries"]), "runtime_ui_appended": True, "runtime_ui_count": len(rows)})
    (DIRECTORY / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DIRECTORY / "runtime-ui-source.txt").write_bytes(report.read_bytes())
    print(json.dumps({"added_runtime_ui": len(rows), "total": manifest["count"], "batches": len(manifest["batches"])}))


if __name__ == "__main__":
    main()
