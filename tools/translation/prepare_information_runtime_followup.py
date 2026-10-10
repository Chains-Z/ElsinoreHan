"""枚举全部信息长短正文，复用治理译文生成编译别名与定向消费者用例。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from analyze import read_json, read_text_assets
from prepare_lead_followup import runtime_source

RESOURCE = Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/resources.assets")


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_rows(resource_bytes):
    """从所有同名 information 资产提取真实 long/short 字段。"""
    rows, assets = [], []
    for name, asset_sha, text in read_text_assets(resource_bytes):
        if name != "information":
            continue
        data = read_json(text)
        assets.append({"asset": name, "asset_sha256": asset_sha, "information_count": len(data["information"])})
        for index, information in enumerate(data["information"]):
            for field in ("long", "short"):
                source = information[field]
                rows.append({"source": source, "runtime_source": runtime_source(source),
                             "origin": {"file": "resources.assets", "asset": name, "asset_sha256": asset_sha,
                                        "json_path": f"$.information[{index}].{field}",
                                        "field": field, "record_id": information["id"]}})
    return rows, assets


def build(rows, translations):
    """只复制准确源条目的治理后译文；不重译，不修改冻结响应。"""
    by_source = {row["source"]: row for row in translations}
    aliases, cases = {}, []
    for index, row in enumerate(rows):
        raw, source = row["source"], row["runtime_source"]
        original = by_source.get(raw)
        if original is None:
            raise ValueError("信息原始正文缺少词表：" + raw[:120])
        target = original["target"]
        if source != raw:
            existing = by_source.get(source)
            if existing is not None and existing["target"] != target:
                raise ValueError("信息运行正文译文与原始治理译文冲突")
            alias = aliases.setdefault(source, {
                "id": "ui-information-runtime-" + digest(source)[:16], "source": source,
                "source_sha256": digest(source), "target": target,
                "existing_id": original["id"], "existing_source": original["source"],
                "existing_source_sha256": digest(original["source"]), "existing_target_sha256": digest(target),
                "origins": [],
                "provenance": "Information LongText/ShortText的真实编译破折号变体，逐字复用治理后的冻结译文",
            })
            alias["origins"].append(row["origin"])
        cases.append({"id": f"information-runtime-{index:03d}-{row['origin']['record_id']}-{row['origin']['field']}",
                      "source": source, "source_sha256": digest(source), "target": target,
                      "target_sha256": digest(target), "origins": [row["origin"]],
                      "verification_level": "真实信息字段的编译运行正文消费者，不代表游戏进度已获得该信息"})
    for alias in aliases.values():
        alias["origins"].append("analysis/ui-audit/information-runtime-source-audit.json")
    return list(aliases.values()), cases


def main():
    translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8-sig"))
    rows, assets = source_rows(RESOURCE.read_bytes())
    aliases, cases = build(rows, translations)
    alias_path = ROOT / "translation/supplemental/information-runtime-aliases.json"
    case_path = ROOT / "runtime/build/information-runtime-followup/consumer-tests.json"
    case_path.parent.mkdir(parents=True, exist_ok=True)
    for path, value in ((alias_path, aliases), (case_path, cases)):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"assets": len(assets), "field_count": len(rows), "aliases": len(aliases),
                      "consumer_cases": len(cases), "case_path": str(case_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
