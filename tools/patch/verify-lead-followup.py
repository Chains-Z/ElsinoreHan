"""严格核对线索完整中文与F8；组件重放和实际已知线索分别报告。"""

import argparse
import base64
import functools
import json
from pathlib import Path
import re

PREFIX = "<line-height=90%>"
ROOT = Path(__file__).resolve().parents[2]


def decode(text):
    return base64.b64decode(text, validate=True).decode("utf-8")


def expected_content(content, groups):
    """按真实同组资源顺序匹配完整段落；支持段落自身的双换行，不靠泛化分词。"""
    results = set()
    for paragraphs in groups.values():
        @functools.lru_cache(None)
        def match(position, first_index):
            found = set()
            for index in range(first_index, len(paragraphs)):
                row = paragraphs[index]
                if not content.startswith(row["source"], position):
                    continue
                end = position + len(row["source"])
                if end == len(content):
                    found.add(row["target"])
                elif content.startswith("\n\n", end):
                    found.update(row["target"] + "\n\n" + tail for tail in match(end + 2, index + 1))
            return frozenset(found)
        results.update(match(0, 0))
    if len(results) != 1:
        raise ValueError("线索正文没有唯一的完整冻结来源")
    return next(iter(results))


def analyze(report, groups, required_replays=None):
    rows = [line.split("\t") for line in report.splitlines() if line]
    source_rows = [row for row in rows if row[0] == "SOURCE"]
    counts = [int(row[1]) for row in rows if row[0] == "EXPECTED_AVAILABLE"]
    expected_replays = {row[2]: decode(row[3]) for row in rows if row[0] == "EXPECTED" and row[1] == "replay"}
    available = [row for row in source_rows if row[1] == "available"]
    replays = [row for row in source_rows if row[1] == "replay"]
    checks = {"finished": ["STATUS", "COMPLETE"] in rows,
              "all_available_leads": len(counts) == 1 and counts[0] > 0 and len(available) == counts[0]
              and len({row[2] for row in available}) == counts[0],
              "all_replay_cases": bool(replays) and len(replays) == len(expected_replays)
              and len({row[2] for row in replays}) == len(replays)
              and {row[2] for row in replays} == set(expected_replays)
              and (required_replays is None or set(expected_replays) == set(required_replays)),
              "full_source_and_translation": True, "active_same_component_three_modes": True,
              "f8_original_exact": True, "f8_restored_exact": True}
    details = []
    for row in source_rows:
        kind, case_id, source = row[1], row[2], decode(row[3])
        try:
            if not source.startswith(PREFIX):
                raise ValueError("真实线高封套缺失")
            expected = PREFIX + expected_content(source[len(PREFIX):], groups)
            if kind == "replay" and expected_replays.get(case_id) != expected:
                raise ValueError("重放预期与原资源不一致")
        except ValueError:
            checks["full_source_and_translation"] = False
            continue
        observed = [item for item in rows if item[0] == "TEXT" and item[1:3] == [kind, case_id]]
        modes = {item[3]: item for item in observed}
        active = len(observed) == 3 and set(modes) == {"translated", "original", "restored"}
        active = active and len({item[4] for item in observed}) == 1 and all(item[5] == "True" for item in observed)
        checks["active_same_component_three_modes"] &= active
        if not active:
            continue
        checks["full_source_and_translation"] &= decode(modes["translated"][6]) == expected
        checks["f8_original_exact"] &= decode(modes["original"][6]) == source
        checks["f8_restored_exact"] &= decode(modes["restored"][6]) == expected
        details.append({"kind": kind, "id": case_id, "source_length": len(source)})
    return {"passed": all(checks.values()), "checks": checks, "available": len(available), "replays": len(replays),
            "details": details, "scope": "真实已知线索按钮与真实资源格式组件重放；不宣称重放条件在游戏中已获取"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    groups = json.loads((ROOT / "translation/supplemental/lead-runtime-manifest.json").read_text(encoding="utf-8"))
    required = {"lead-screenshot-hamlet", "lead-screenshot-spy", "lead-screenshot-father",
                "lead-single-chambers_1", "lead-single-book_complete", "lead-all-14", "lead-all-13", "lead-all-12"}
    result = analyze(args.report.read_text(encoding="utf-8"), groups, required)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
