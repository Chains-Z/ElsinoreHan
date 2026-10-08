"""离线核对扩展样本的真实来源、输入顺序和去重契约。"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "analysis"), str(ROOT / "tools/translation")]
import analyze
import prepare_pilot


def resolve_path(value, path):
    """按清单里的显式对象 ID 或数组索引定位真实 JSON 字段。"""
    for step in path.split("."):
        match = re.fullmatch(r"([A-Za-z_]+)(?:\[([^\]]+)\])?", step)
        if match is None:
            raise ValueError("不支持的来源路径")
        key, selector = match.groups()
        value = value[key]
        if selector is not None:
            if selector.isdigit():
                value = value[int(selector)]
            else:
                field, expected = selector.split("=", 1)
                candidates = [item for item in value if item.get(field) == expected]
                if len(candidates) != 1:
                    raise ValueError("对象 ID 不唯一")
                value = candidates[0]
    return value


def verify_contract(manifest, inputs, old_messages):
    """检查来源哈希和 VNText 丢失元数据时的稳定关联。"""
    rows = manifest["entries"]
    if len(rows) != 300 or manifest["count"] != 300:
        raise ValueError("样本数量不符")
    if Counter(row["category"] for row in rows) != {"dialogue": 180, "challenge": 60, "ui": 60}:
        raise ValueError("分层数量不符")
    norms = [analyze.normalize(row["message"]) for row in rows]
    if len(set(norms)) != len(norms) or set(norms).intersection(map(analyze.normalize, old_messages)):
        raise ValueError("新旧样本存在重复")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("来源 ID 重复")
    for row in rows:
        if row["source_text_sha256"] != hashlib.sha256(row["message"].encode()).hexdigest():
            raise ValueError("原文哈希不符")
    covered = []
    for batch in manifest["batches"]:
        members = [row for row in rows if row["batch"] == batch["id"]]
        expected = [{key: row[key] for key in ("name", "message") if row[key] is not None} for row in members]
        if inputs[batch["file"]] != expected or batch["count"] != len(members):
            raise ValueError("输入内容或数量不符")
        for index, row in enumerate(members):
            if row["index"] != index or row["file"] != batch["file"]:
                raise ValueError("来源关联顺序不符")
        covered.extend(members)
    if len(covered) != len(rows):
        raise ValueError("批次遗漏条目")


def main():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    old = json.loads((ROOT / "translation/trial-2026-10-09/manifest.json").read_text(encoding="utf-8"))
    inputs = {batch["file"]: json.loads((OUT / "inputs" / batch["file"]).read_text(encoding="utf-8")) for batch in manifest["batches"]}
    verify_contract(manifest, inputs, [row["message"] for row in old["entries"]])
    assets = {(name, digest): body for name, digest, body in analyze.read_text_assets((analyze.GAME / "resources.assets").read_bytes())}
    names_body = assets[("name_mapping", manifest["name_mapping_asset_sha256"])]
    names = analyze.read_json(names_body)
    scene_digest = next(row["source_asset_sha256"] for row in manifest["entries"] if row["id"].startswith("scenes:"))
    dialogues = {row["source_line"]: row for row in prepare_pilot.read_dialogues(assets[("scenes", scene_digest)], scene_digest, names)}
    for row in manifest["entries"]:
        name = row["id"].split(":", 1)[0]
        body = assets[(name, row["source_asset_sha256"])]
        if body.splitlines()[row["source_line"]-1] != row["source_raw_line"]:
            raise ValueError("原始行不符")
        if name == "scenes":
            actual = dialogues[row["source_line"]]
            if any(actual[key] != row[key] for key in ("id", "message", "name", "speaker_id", "scene", "acting_cues")):
                raise ValueError("真实对白字段不符")
        elif resolve_path(analyze.read_json(body), row["source_json_path"]) != row["message"]:
            raise ValueError("真实资料字段不符")
    for batch in manifest["batches"]:
        rules = json.loads((OUT / "rules" / (batch["id"] + ".json")).read_text(encoding="utf-8"))
        if re.search(r"[\u3400-\u9fff]", rules["qwen_mt_domains"]):
            raise ValueError("Qwen domains 包含非英文说明")
    print(json.dumps({"entries": 300, "source_fields_verified": 300, "input_batches_verified": len(inputs), "old_sample_overlap": 0, "model_calls": 0}, ensure_ascii=True))


if __name__ == "__main__":
    main()
