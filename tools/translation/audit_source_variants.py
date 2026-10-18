"""检查资源对白、编译变体与显式运行别名；已审定措辞差异以双译文哈希固定。"""

import argparse
import hashlib
import json
import re

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, read, save


BASELINE = ROOT / "translation/supplemental/source-variant-reviewed-differences.json"
OUTPUT = ROOT / "runtime/build/source-variant-review/audit.json"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compare_targets(actor, resource_target, runtime_target):
    """只剥离幽灵编译新增的一层斜体，保留原有句内强调和标点。"""
    missing_outer = False
    comparable = runtime_target
    if actor == "ghost":
        if comparable.startswith("<i>") and comparable.endswith("</i>"):
            comparable = comparable[3:-4]
        else:
            missing_outer = True
    same_text = re.sub(r"<[^>]+>", "", resource_target) == re.sub(r"<[^>]+>", "", comparable)
    return {
        "equal": resource_target == comparable and not missing_outer,
        "formatting_only": same_text and not missing_outer,
        "missing_runtime_outer_italic": missing_outer,
        "comparable_runtime_target": comparable,
    }


def signature(row):
    """双源及双译文分别绑定，单边更新也必须重新审查。"""
    return {key: digest(row[value]) for key, value in (
        ("source_sha256", "source"), ("runtime_source_sha256", "runtime_source"),
        ("resource_target_sha256", "resource_target"), ("runtime_target_sha256", "runtime_target"))}


def is_reviewed(row, baseline):
    return all(baseline.get(key) == value for key, value in signature(row).items())


def collect_pairs(translations, dialogue, compiled_sources):
    by_source = {row["source"]: row for row in translations}
    pairs, exclusions, missing = [], [], []
    seen = set()
    for row in dialogue:
        raw, runtime = row["source"], row["runtime_source"]
        if raw == runtime:
            continue
        key = (row["actor"], raw, runtime)
        if key in seen:
            continue
        seen.add(key)
        raw_key = raw if raw in by_source else raw.strip()
        if raw_key not in by_source or runtime not in by_source:
            if not re.search(r"[A-Za-z0-9\u3400-\u9fff]", raw):
                reason = "纯停顿，不属于需要翻译的词句"
            elif runtime not in compiled_sources:
                reason = "资源旧场景未进入当前编译程序集，不推测补出运行词条"
            else:
                missing.append({"source": raw, "runtime_source": runtime, "origins": row["origins"]})
                continue
            exclusions.append({"source": raw, "runtime_source": runtime, "reason": reason,
                               "origins": row["origins"]})
            continue
        resource, actual = by_source[raw_key], by_source[runtime]
        pairs.append({
            "actor": row["actor"], "source": raw, "runtime_source": runtime,
            "resource_id": resource["id"], "runtime_id": actual["id"],
            "resource_lookup_trimmed": raw_key != raw,
            "resource_target": resource["target"], "runtime_target": actual["target"],
            "origins": row["origins"],
            **compare_targets(row["actor"], resource["target"], actual["target"]),
        })
    return pairs, exclusions, missing


def audit_aliases(translations, entries):
    by_source = {row["source"]: row for row in translations}
    checked, mismatches = 0, []
    for entry in entries:
        if "existing_source" not in entry:
            continue
        alias, base = by_source.get(entry["source"]), by_source.get(entry["existing_source"])
        if alias is None or base is None:
            mismatches.append({"source": entry["source"], "reason": "显式别名或基本词条缺失"})
            continue
        checked += 1
        expected = entry.get("runtime_prefix", "") + base["target"]
        if alias["target"] != expected:
            mismatches.append({"source": alias["source"], "expected": expected, "target": alias["target"]})
    return checked, mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-reviewed-baseline", action="store_true",
                        help="仅在逐项人工审查完成后记录当前允许差异；默认不会改写基线")
    args = parser.parse_args()
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    dialogue, _ = extract_rows(translations)
    compiled = {row["source"] for row in read(ROOT / "analysis/ui-audit/assembly-strings.json")}
    pairs, exclusions, missing = collect_pairs(translations, dialogue, compiled)
    differences = [row for row in pairs if not row["equal"]]
    if args.write_reviewed_baseline:
        decisions = []
        for row in differences:
            kind = "formatting_only" if row["formatting_only"] else "equivalent_wording"
            reason = "已逐项对照英文与两版中文，当前差异不改变此处主要含义；不为字面一致重写正常译文"
            if row["source"] == "I do.":
                kind = "shared_source_context"
                reason = "裸源共享于多种简短应答，幽灵变体按其实际情境答是的我也一样，不强制共用一种中文"
            decisions.append({"resource_id": row["resource_id"], "runtime_id": row["runtime_id"],
                              **signature(row), "kind": kind, "reason": reason})
        save(BASELINE, decisions)
    baseline = {(row["resource_id"], row["runtime_id"]): row for row in read(BASELINE)} if BASELINE.exists() else {}
    unreviewed = [row for row in differences if not is_reviewed(
        row, baseline.get((row["resource_id"], row["runtime_id"]), {}))]
    entries = []
    for path in sorted((ROOT / "translation/supplemental").glob("*.json")):
        data = read(path)
        if isinstance(data, list):
            entries.extend(entry for entry in data if isinstance(entry, dict))
    aliases_checked, alias_mismatches = audit_aliases(translations, entries)
    result = {
        "dialogue_rows": len(dialogue), "paired_rows": len(pairs),
        "equal_pairs": len(pairs) - len(differences), "reviewed_differences": len(differences) - len(unreviewed),
        "unreviewed_differences": len(unreviewed), "aliases_checked": aliases_checked,
        "alias_mismatches": alias_mismatches, "missing": missing, "exclusions": exclusions,
        "pairs": pairs, "unreviewed": unreviewed,
        "passed": not (unreviewed or missing or alias_mismatches),
        "limitations": ["已检查成对变体的差异，不等同所有对白完整语义或全部剧情E2E审校"],
    }
    save(OUTPUT, result)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("pairs", "unreviewed", "exclusions")}, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit("检测到新的双源差异、缺失或运行别名未同步")


if __name__ == "__main__":
    main()
