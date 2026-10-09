"""从完整线索资源生成运行源别名与限定多段规则，不改冻结译文或游戏状态。"""

import hashlib
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "translation/supplemental"
REPLACEMENTS = (" -- ", " --- ", " - ", "-- ", "--- ", " --", " ---", "--", "---")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def runtime_source(source):
    """复现已核实CompilerPasses对LeadLine.Text的九步替换。"""
    for old in REPLACEMENTS:
        source = source.replace(old, "—")
    return source


def build(resources, translations):
    """只收同组线索正文，用真实段落组成夹具；夹具不代表已获取的游戏进度。"""
    by_source = {row["source"]: row for row in translations}
    groups, aliases = {}, []
    for resource in resources:
        origin = resource["origin"]
        if origin.get("asset") != "leads" or origin.get("field") != "text":
            continue
        raw = resource["source"]
        if digest(raw) != resource["source_sha256"]:
            raise ValueError("线索资源源哈希不符")
        original = by_source.get(raw) or by_source.get(raw.strip())
        if original is None:
            raise ValueError("线索缺少冻结译文：" + origin["record_id"])
        source = runtime_source(raw)
        target = original["target"]
        if source != raw:
            if source in by_source and by_source[source]["target"] != target:
                raise ValueError("线索运行别名已有冲突译文")
            aliases.append({
                "id": "ui-lead-runtime-" + digest(source)[:16], "source": source, "target": target,
                "source_sha256": digest(source), "origins": [origin, "analysis/ui-audit/lead-followup-il.json"],
                "existing_id": original["id"], "existing_source": original["source"],
                "existing_source_sha256": digest(original["source"]), "existing_target_sha256": digest(target),
                "provenance": "真实LeadLine编译破折号变体，逐字复用冻结译文，不改原资源或进度",
            })
        match = re.fullmatch(r"\$\.list\[(\d+)\]\.lines\[(\d+)\]\.text", origin["json_path"])
        if not match:
            raise ValueError("线索正文资源路径未识别")
        groups.setdefault(int(match[1]), []).append({"line_index": int(match[2]), "line_id": origin["record_id"],
                                                    "source": source, "target": target, "origin": origin,
                                                    "translation_id": original["id"]})
    rules, cases = [], []

    def add_case(case_id, parts, prefix="", target_override=False):
        source = prefix + "\n\n".join(row["source"] for row in parts)
        target = None if target_override else prefix + "\n\n".join(row["target"] for row in parts)
        cases.append({"id": case_id, "source": source, "source_sha256": digest(source), "target": target,
                      "target_sha256": digest(target) if target is not None else None,
                      "origins": [row["origin"] for row in parts],
                      "verification_level": "真实资源的格式组件组合，不宣称相应游戏进度已获取"})

    for group_id, paragraphs in sorted(groups.items()):
        paragraphs.sort(key=lambda row: row["line_index"])
        union = "(?:" + "|".join(re.escape(row["source"]) for row in sorted(paragraphs, key=lambda row: -len(row["source"]))) + ")"
        rules.append({
            "id": "ui-rule-lead-paragraphs-" + str(group_id), "priority": 85,
            "pattern": r"^(?<prefix_i><line-height=90%>)?(?<first>" + union + r")(?<separator_i>\n\n)(?<rest>" + union + r"(?:\n\n" + union + r")*)\z$",
            "replacement": "${prefix_i}${first}${separator_i}${rest}",
            "origins": ["analysis/ui-audit/lead-followup-il.json", paragraphs[0]["origin"]],
            "note": "限定同组真实线索段落及完整双换行；递归消费全部正文，未知段落失败，保留原译文和段距",
        })
        for paragraph in paragraphs:
            add_case("lead-single-" + paragraph["line_id"], [paragraph], "<line-height=90%>")
        for left, right in itertools.combinations(paragraphs, 2):
            add_case("lead-pair-" + left["line_id"] + "-" + right["line_id"], [left, right], "<line-height=90%>")
        add_case("lead-all-" + str(group_id), paragraphs, "<line-height=90%>")
        add_case("lead-bare-all-" + str(group_id), paragraphs)
        unknown = {"source": "Unknown internal lead identifier", "target": "", "origin": {"fixture": "未知源拒绝"}}
        add_case("lead-unknown-" + str(group_id), [paragraphs[0], unknown], target_override=True)
    for case_id, ids in (("lead-screenshot-hamlet", ("hamlet_1", "hamlet_3b", "hamlet_5")),
                         ("lead-screenshot-spy", ("spy_1b", "spy_2", "spy_3")),
                         ("lead-screenshot-father", ("father_1", "father_1a", "father_3"))):
        by_id = {row["line_id"]: row for rows in groups.values() for row in rows}
        if not all(line_id in by_id for line_id in ids):
            raise ValueError("截图线索ID未核实：" + case_id)
        add_case(case_id, [by_id[line_id] for line_id in ids], "<line-height=90%>")
    return aliases, rules, cases, groups


def main():
    import argparse
    import base64
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-cases", type=Path, help="另写8个已审真实资源组合的临时组件重放TSV")
    args = parser.parse_args()
    resource_path = ROOT / "analysis/ui-audit/resource-strings.json"
    resources = json.loads(resource_path.read_text(encoding="utf-8-sig"))
    translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
    aliases, rules, cases, groups = build(resources, translations)
    for filename, value in (("lead-runtime-aliases.json", aliases), ("lead-followup-rules.json", rules), ("lead-followup-tests.json", cases)):
        (OUT / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = {str(key): value for key, value in groups.items()}
    (OUT / "lead-runtime-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.runtime_cases:
        selected = {"lead-screenshot-hamlet", "lead-screenshot-spy", "lead-screenshot-father",
                    "lead-single-chambers_1", "lead-single-book_complete", "lead-all-14", "lead-all-13", "lead-all-12"}
        replay = [row for row in cases if row["id"] in selected]
        if len(replay) != len(selected):
            raise ValueError("组件重放缺少已审真实线索组合")
        def b64(value):
            return base64.b64encode(value.encode("utf-8")).decode("ascii")
        args.runtime_cases.parent.mkdir(parents=True, exist_ok=True)
        args.runtime_cases.write_text("".join(row["id"] + "\t" + b64(row["source"].removeprefix("<line-height=90%>"))
                                             + "\t" + b64(row["target"]) + "\n" for row in replay), encoding="utf-8", newline="\n")
    print(json.dumps({"groups": len(groups), "paragraphs": sum(map(len, groups.values())), "aliases": len(aliases),
                      "rules": len(rules), "cases": len(cases)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
