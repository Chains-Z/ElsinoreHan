"""核对全文 Sol 结果并导出 XUnity 离线词表；禁止带缺条发布。"""

import hashlib
import json
from pathlib import Path
import re

from run_sol_full import load_exclusions, validate

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "translation" / "sol-full-2026-10-09"


def encode(text):
    """匹配上游解码器，额外避免双斜杠被视为行内注释。"""
    text = text.replace("\\", "\\\\").replace("=", "\\=").replace("\r", "\\r").replace("\n", "\\n")
    return text.replace("//", "\\u002f\\u002f").replace("%3D", "\\u00253D")


def format_rule(source, target):
    """将真实数字参数模板转换为有明确锚点的Splitter，教程按键不再翻译。"""
    parameter = re.compile(r"\{([0-9]+)(?::[^{}]+)?\}")
    matches = list(parameter.finditer(source))
    if not matches or len(parameter.sub("", source)) < 10:
        return None
    preserve_args = "Try pressing" in source or "Try holding" in source or "Press {" in source or "press {" in source
    groups = {match[1]: "arg" + match[1] + ("_i" if preserve_args else "") for match in matches}
    parts, seen, position = ["^"], set(), 0
    for match in matches:
        parts.append(re.escape(source[position:match.start()]))
        group = groups[match[1]]
        parts.append("\\k<" + group + ">" if group in seen else "(?<" + group + ">[\\s\\S]*?)")
        seen.add(group)
        position = match.end()
    parts.extend([re.escape(source[position:]), "$"])
    replacement = parameter.sub(lambda match: "${" + groups[match[1]] + "}", target)
    return {"pattern": "".join(parts), "replacement": replacement, "preserve_args": preserve_args}


def main():
    manifest = json.loads((DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
    exclusions = load_exclusions(DIRECTORY)
    corrections_path = DIRECTORY / "local-corrections.json"
    corrections = json.loads(corrections_path.read_text(encoding="utf-8")) if corrections_path.exists() else []
    correction_map = {row["id"]: row for row in corrections}
    targets = {}
    for batch in manifest["batches"]:
        source_path = DIRECTORY / "inputs" / (batch["id"] + ".json")
        output_path = DIRECTORY / "outputs" / (batch["id"] + ".json")
        if not output_path.is_file():
            raise SystemExit("全文仍缺批次：" + batch["id"])
        source = json.loads(source_path.read_text(encoding="utf-8"))
        value = json.loads(output_path.read_text(encoding="utf-8"))
        raw = json.loads((DIRECTORY / "raw" / (batch["id"] + ".json")).read_text(encoding="utf-8"))
        raw_map = {row["id"]: row["target"] for row in raw["translations"]}
        for row in value["translations"]:
            if row["target"] != raw_map[row["id"]]:
                correction = correction_map.get(row["id"])
                if not correction or correction["original_target"] != raw_map[row["id"]] or correction["corrected_target"] != row["target"]:
                    raise SystemExit("存在未记录的译文修改：" + row["id"])
        errors = validate(source, value, exclusions)
        if errors:
            raise SystemExit("全文校验失败：" + json.dumps(errors, ensure_ascii=True))
        audit = json.loads((DIRECTORY / "audit" / (batch["id"] + ".json")).read_text(encoding="utf-8"))
        if audit.get("state") != "passed" or audit.get("model") != "gpt-6.1-sol":
            raise SystemExit("缺少Sol真实成功记录：" + batch["id"])
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != audit["source_sha256"]:
            raise SystemExit("源批次与执行时哈希不符：" + batch["id"])
        for row in value["translations"]:
            if row["id"] in targets:
                raise SystemExit("重复译文ID")
            targets[row["id"]] = row["target"]
    assert len(targets) == manifest["count"]
    rows = []
    for entry in manifest["entries"]:
        assert hashlib.sha256(entry["source"].encode("utf-8")).hexdigest() == entry["source_sha256"]
        if entry["id"] in exclusions:
            assert exclusions[entry["id"]] == entry["source_sha256"]
            continue
        rows.append({"id": entry["id"], "source": entry["source"], "target": targets[entry["id"]], "batch": entry["batch"]})
    (DIRECTORY / "translations.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package = ROOT / "runtime" / "package" / "ElsinoreHan-Sol" / "BepInEx" / "Translation" / "zh-CN" / "Text"
    package.mkdir(parents=True, exist_ok=True)
    dictionary = package / "ElsinoreHan-Sol.txt"
    dictionary.write_text("\n".join(encode(row["source"]) + "=" + encode(row["target"]) for row in rows) + "\n", encoding="utf-8")
    dynamic = []
    for row in rows:
        rule = format_rule(row["source"], row["target"])
        if rule:
            dynamic.append({"id": row["id"], "source": row["source"], "target": row["target"], **rule,
                            "encoded_line": encode('sr:"' + rule["pattern"] + '"') + "=" + encode('"' + rule["replacement"] + '"')})
    (DIRECTORY / "dynamic-rules.json").write_text(json.dumps(dynamic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dynamic_path = package / "ElsinoreHan-Dynamic.txt"
    dynamic_path.write_text("\n".join(row["encoded_line"] for row in dynamic) + "\n", encoding="utf-8")
    characters = "".join(sorted({char for row in rows for char in row["target"] if "\u3400" <= char <= "\u9fff"}))
    (DIRECTORY / "chinese-characters.txt").write_text(characters, encoding="utf-8")
    notices = []
    for row in rows:
        if re.search(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b", row["target"]):
            notices.append({"id": row["id"], "source": row["source"], "target": row["target"], "reason": "译文含连续英文词，可能是专名/引文，也可能局部漏译，需核对"})
    (DIRECTORY / "english-review-notices.json").write_text(json.dumps(notices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0}
    for path in (DIRECTORY / "audit").glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        for key in usage:
            usage[key] += record.get("usage", {}).get(key, 0)
    names_audit = DIRECTORY / "names-job" / "audit" / "b0000.json"
    if names_audit.exists():
        record = json.loads(names_audit.read_text(encoding="utf-8"))
        for key in usage:
            usage[key] += record.get("usage", {}).get(key, 0)
    proof = {"model": "gpt-6.1-sol", "count": len(rows), "submitted_candidates": manifest["count"], "excluded_nontext": len(exclusions), "batches": len(manifest["batches"]),
             "id_count_order_source_hashes_and_markers_passed": True,
             "dictionary_path": str(dictionary.relative_to(ROOT)), "dictionary_sha256": hashlib.sha256(dictionary.read_bytes()).hexdigest(),
             "dynamic_dictionary_sha256": hashlib.sha256(dynamic_path.read_bytes()).hexdigest(),
             "recorded_codex_usage_including_names": usage, "english_review_notices": len(notices),
             "dynamic_format_rules": len(dynamic), "unique_chinese_characters": len(characters),
             "local_recorded_corrections": len(corrections), "all_outputs_match_raw_or_recorded_correction": True,
             "limitations": ["正文来自真实Sol执行，不是百炼或人工虚构输出", "完整性通过不代表全分支意义和文风无误", "尚未声明游戏内对白排版通过", "没有观测订阅周额度的实际扣减"]}
    (DIRECTORY / "verification.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, ensure_ascii=True))


if __name__ == "__main__":
    main()
