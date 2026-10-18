"""核对全文 Sol 结果并导出 XUnity 离线词表；禁止带缺条发布。"""

import hashlib
import json
from pathlib import Path
import re

from run_sol_full import load_exclusions, validate

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "translation" / "sol-full-2026-10-09"
SUPPLEMENTAL = ROOT / "translation" / "supplemental" / "ui-translations.json"


def apply_supplemental(rows, entries):
    """合并有来源的定向补译；已有译文必须明确记录旧值，冻结模型响应保持原样。"""
    result = [dict(row) for row in rows]
    by_source = {row["source"]: row for row in result}
    by_id = {row["id"]: row for row in result}
    seen = set()
    for entry in entries:
        source = entry["source"]
        if source in seen or not entry.get("origins") or hashlib.sha256(source.encode("utf-8")).hexdigest() != entry["source_sha256"]:
            raise ValueError("补译来源、哈希或唯一性不完整")
        seen.add(source)
        if entry["id"].startswith("mixed-log-terminal-"):
            base = by_source.get(entry.get("base_source"))
            if (base is None or source != base["source"] + "\n"
                    or entry.get("base_target_sha256") != hashlib.sha256(base["target"].encode("utf-8")).hexdigest()
                    or entry["target"] != base["target"] + "\n"):
                raise ValueError("日志尾LF别名必须逐字复用真实通知原子")
        if "existing_id" in entry:
            original = by_id.get(entry["existing_id"])
            prefix = entry.get("runtime_prefix", "")
            if prefix and (prefix != "<line-height=90%>" or original is None
                           or source != prefix + original["source"]):
                raise ValueError("对白运行别名必须使用真实行高封套和原句")
            if (original is None or entry.get("existing_source") != original["source"]
                    or entry.get("existing_source_sha256") != hashlib.sha256(original["source"].encode("utf-8")).hexdigest()
                    or entry.get("existing_target_sha256") != hashlib.sha256(original["target"].encode("utf-8")).hexdigest()
                    or entry["target"] != prefix + original["target"]):
                raise ValueError("精确源别名必须完整复用已记录的原条目及译文")
        if not re.search(r"[\u3400-\u9fff]", entry["target"]) or validate([entry], {"translations": [{"id": entry["id"], "target": entry["target"]}]}):
            raise ValueError("补译内容或格式不完整")
        if source in by_source:
            row = by_source[source]
            if entry.get("previous_target") != row["target"]:
                raise ValueError("已有译文补修缺少准确旧值")
            row["target"] = entry["target"]
            row["supplement_id"] = entry["id"]
        else:
            row = {key: entry[key] for key in ("id", "source", "target")}
            row["batch"] = "settings-supplemental"
            result.append(row)
            by_source[source] = row
            by_id[row["id"]] = row
    return result


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


def printf_rule(source, target):
    """覆盖已审核的F# %s界面模板，将真实运行参数交给递归离线词表。"""
    if "%s" not in source or source.count("%s") != target.count("%s"):
        return None
    def convert(text):
        parts = text.split("%s")
        return "".join(part + ("{" + str(index) + "}" if index < len(parts) - 1 else "") for index, part in enumerate(parts)).replace("%%", "%")
    format_source, format_target = convert(source), convert(target)
    rule = format_rule(format_source, format_target)
    return {**rule, "format_source": format_source, "format_target": format_target} if rule else None


def render_ui_rule(rule):
    """只编译已审日志连续项的精确标点分支与换行前空白，拒绝其它规则借用。"""
    result = dict(rule)
    padding = rule.get("continuation_separator_padding", False)
    punctuation = rule.get("continuation_punctuation", [])
    if not padding and not punctuation:
        return result
    if rule["id"] != "ui-rule-log-frozen-continuation" or padding is not True or punctuation != ["..."]:
        raise ValueError("日志连续项编译选项超出已审范围")
    marker = r")(?<newline_i>\n)"
    if result["pattern"].count(marker) != 1:
        raise ValueError("冻结日志规则的唯一换行边界不符")
    result["pattern"] = result["pattern"].replace(marker, r"|\.\.\.)(?<newline_i>[ \t]*\n)")
    return result


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
    base_count = len(rows)
    # 新的正文校订只在导出层应用；冻结输出和原始模型响应保持不变。
    export_corrections = []
    for correction in corrections:
        if correction.get("apply_at_export") is not True:
            continue
        original = next((row for row in rows if row["id"] == correction["id"]), None)
        if original is None or correction["source"] != original["source"]:
            raise ValueError("正文导出校订的稳定ID或原文不符")
        export_corrections.append({"id": correction["id"], "source": correction["source"],
                                   "source_sha256": correction["source_sha256"],
                                   "previous_target": correction["original_target"],
                                   "target": correction["corrected_target"], "origins": correction["origins"]})
    rows = apply_supplemental(rows, export_corrections)
    supplemental = json.loads(SUPPLEMENTAL.read_text(encoding="utf-8")) if SUPPLEMENTAL.exists() else []
    rows = apply_supplemental(rows, supplemental)
    for filename in ("playmaster-corrections.json", "knight-guard-corrections.json", "irma-corrections.json", "dialect-corrections.json",
                     "court-title-corrections.json", "dialogue-context-corrections.json", "reading-document-corrections.json",
                     "timeline-label-corrections.json", "brit-name-corrections.json", "love-context-corrections.json",
                     "curtain-call-corrections.json", "ending-marriage-corrections.json"):
        terminology_path = SUPPLEMENTAL.with_name(filename)
        if terminology_path.exists():
            terminology = json.loads(terminology_path.read_text(encoding="utf-8"))
            rows = apply_supplemental(rows, terminology)
            supplemental += terminology
    for filename in ("notification-translations.json", "runtime-closeup-translations.json", "hamlet-bio-alias.json", "bio-runtime-aliases.json", "lead-runtime-aliases.json", "information-runtime-aliases.json", "dialogue-log-runtime-aliases.json", "dialogue-runtime-aliases.json", "mixed-log-translations.json", "ending-book-translations.json", "credits-skip-translations.json"):
        extra_path = SUPPLEMENTAL.with_name(filename)
        if extra_path.exists():
            extra_entries = json.loads(extra_path.read_text(encoding="utf-8"))
            # 后续校订须匹配上轮译文，保持每层来源唯一和覆盖链可审计。
            rows = apply_supplemental(rows, extra_entries)
            supplemental += extra_entries
    # 姓名统一在历史别名治理之后应用，并显式覆盖基本词条和受影响别名。
    name_path = SUPPLEMENTAL.with_name("shakespeare-name-corrections.json")
    if name_path.exists():
        names = json.loads(name_path.read_text(encoding="utf-8"))
        rows = apply_supplemental(rows, names)
        supplemental += names
    for filename in ("ending-style-corrections.json", "ghost-regret-corrections.json", "source-variant-corrections.json"):
        style_path = SUPPLEMENTAL.with_name(filename)
        if style_path.exists():
            styles = json.loads(style_path.read_text(encoding="utf-8"))
            rows = apply_supplemental(rows, styles)
            supplemental += styles
    (DIRECTORY / "translations.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package = ROOT / "runtime" / "package" / "ElsinoreHan-Sol" / "BepInEx" / "Translation" / "zh-CN" / "Text"
    package.mkdir(parents=True, exist_ok=True)
    dictionary = package / "ElsinoreHan-Sol.txt"
    dictionary.write_text("\n".join(encode(row["source"]) + "=" + encode(row["target"]) for row in rows) + "\n", encoding="utf-8")
    dynamic = []
    for row in rows:
        rule = format_rule(row["source"], row["target"]) or printf_rule(row["source"], row["target"])
        if rule:
            dynamic.append({"id": row["id"], "source": row["source"], "target": row["target"], **rule,
                            "encoded_line": encode('sr:"' + rule["pattern"] + '"') + "=" + encode('"' + rule["replacement"] + '"')})
    ui_rules_path = ROOT / "translation" / "supplemental" / "dynamic-ui-rules.json"
    ui_rules = json.loads(ui_rules_path.read_text(encoding="utf-8")) if ui_rules_path.exists() else []
    for filename in ("notification-ui-rules.json", "lead-followup-rules.json", "biography-followup-rules.json", "map-ui-rules.json",
                     "timeline-followup-rules.json", "nested-belief-followup-rules.json", "dialogue-log-followup-rules.json", "mixed-log-rules.json", "ambient-log-followup-rules.json"):
        followup_path = ui_rules_path.with_name(filename)
        if followup_path.exists():
            ui_rules += json.loads(followup_path.read_text(encoding="utf-8"))
    # XUnity 逆序取首个匹配；结构边界必须优先于宽泛的姓名/富文本封套。
    ui_rules = sorted(ui_rules, key=lambda rule: rule.get("priority", 0))
    for rule in ui_rules:
        rule = render_ui_rule(rule)
        if not rule.get("origins") or not rule["pattern"].startswith("^") or not rule["pattern"].endswith("$"):
            raise ValueError("动态UI规则必须有真实来源和全串锚点")
        dynamic.append({**rule, "kind": "recursive_ui_splitter", "encoded_line": encode('sr:"' + rule["pattern"] + '"') + "=" + encode('"' + rule["replacement"] + '"')})
    (DIRECTORY / "dynamic-rules.json").write_text(json.dumps(dynamic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dynamic_path = package / "ElsinoreHan-Dynamic.txt"
    dynamic_path.write_text("\n".join(row["encoded_line"] for row in dynamic) + "\n", encoding="utf-8")
    displayed_targets = [row["target"] for row in rows] + [rule["replacement"] for rule in dynamic]
    characters = "".join(sorted({char for target in displayed_targets for char in target if "\u3400" <= char <= "\u9fff"}))
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
             "base_translation_count": base_count, "supplemental_entries": len(supplemental), "supplemental_new_sources": len(rows) - base_count,
             "id_count_order_source_hashes_and_markers_passed": True,
             "dictionary_path": str(dictionary.relative_to(ROOT)), "dictionary_sha256": hashlib.sha256(dictionary.read_bytes()).hexdigest(),
             "dynamic_dictionary_sha256": hashlib.sha256(dynamic_path.read_bytes()).hexdigest(),
             "recorded_codex_usage_including_names": usage, "english_review_notices": len(notices),
             "dynamic_format_rules": len(dynamic), "unique_chinese_characters": len(characters),
             "recursive_ui_rules": len(ui_rules),
             "local_recorded_corrections": len(corrections), "all_outputs_match_raw_or_recorded_correction": True,
             "limitations": ["正文来自真实Sol执行，不是百炼或人工虚构输出", "完整性通过不代表全分支意义和文风无误", "尚未声明游戏内对白排版通过", "没有观测订阅周额度的实际扣减"]}
    (DIRECTORY / "verification.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, ensure_ascii=True))


if __name__ == "__main__":
    main()
