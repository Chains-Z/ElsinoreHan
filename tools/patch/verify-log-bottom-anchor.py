"""核验真实日志末尾的F8切换及手动离开末尾，不以段落恢复代替底部恢复。"""

import argparse
import base64
import json
import math
from pathlib import Path


def analyze(report, journal):
    checks = {name: False for name in ("complete_three_cases", "real_history_and_text", "fresh_toggle_completion",
              "both_languages_stay_at_bottom", "manual_scroll_uses_paragraph_anchor")}
    details = []
    try:
        rows = [line.split("\t") for line in report.splitlines() if line]
        if any(row[0] not in {"SCHEMA", "SAMPLE", "STATUS"} or len(row) != (15 if row[0] == "SAMPLE" else 2) for row in rows):
            return {"passed": False, "checks": checks, "cases": details}
        samples = [row for row in rows if row[0] == "SAMPLE"]
        names = ("bottom-to-original", "bottom-to-translated", "manual-away")
        keyed = {(row[1], row[2]): row for row in samples}
        checks["complete_three_cases"] = (rows[0] == ["SCHEMA", "1"] and rows[-1] == ["STATUS", "COLLECTED"]
            and len(samples) == len(keyed) == 6 and set(keyed) == {(name, stage) for name in names for stage in ("before", "after")})
        if not checks["complete_three_cases"]:
            return {"passed": False, "checks": checks, "cases": details}
        journal_rows = [line.split("\t") for line in journal.splitlines() if line]
        dec = lambda value: base64.b64decode(value, validate=True).decode("utf-8")
        history = {int(row[1]): dec(row[2]) for row in journal_rows if row[0] == "HISTORY_SOURCE"}
        entries = {int(row[1]): row[2] for row in journal_rows if row[0] == "LOG_ENTRY"}
        entry_ids = set(entries.values())
        targets = {row[3]: dec(row[5]) for row in journal_rows
                   if row[:3] == ["TEXT", "log", "translated"] and row[3] in entry_ids}
        for name in checks:
            checks[name] = True
        for name in names:
            before, after = keyed[(name, "before")], keyed[(name, "after")]
            index = int(before[6])
            checks["real_history_and_text"] &= (index in history and before[6:8] == after[6:8]
                and entries.get(index) == before[7] and before[7] in targets and before[7] != "0"
                and dec(before[13]) == dec(after[13]) == history.get(index))
            for row in (before, after):
                checks["real_history_and_text"] &= row[3] in {"True", "False"} and dec(row[14]) == (
                    targets.get(row[7]) if row[3] == "True" else history.get(int(row[6])))
            initial_mode = "False" if name == "bottom-to-translated" else "True"
            checks["fresh_toggle_completion"] &= (before[3] == initial_mode and after[3] != before[3]
                and int(after[8]) > int(before[8]) and before[10] == "captured")
            numbers = [float(row[col]) for row in (before, after) for col in (4, 5, 12)]
            finite = all(math.isfinite(value) for value in numbers)
            if name != "manual-away":
                checks["both_languages_stay_at_bottom"] &= (finite and all(0 <= float(row[5]) <= 1 for row in (before, after))
                    and before[9] == after[9] == "True" and after[10] == "bottom-restored" and 0 <= float(after[12]) <= 1)
            else:
                checks["manual_scroll_uses_paragraph_anchor"] &= (finite and abs(float(before[4]) - 0.35) <= 0.0001
                    and 0.01 < float(after[4]) < 0.99 and before[9] == after[9] == "False"
                    and before[11] == after[11] and after[10] == "restored" and 0 <= float(after[12]) <= 1)
            details.append({"case": name, "history_index": index, "bottom_distance_before": float(before[5]),
                            "bottom_distance_after": float(after[5]), "outcome": after[10]})
    except (ValueError, TypeError, IndexError, KeyError, UnicodeError, OverflowError):
        checks["complete_three_cases"] = False
    return {"passed": all(checks.values()), "checks": checks, "cases": details,
            "limitations": ["真实冻结历史、正式共享F8路径及ScrollRect组件几何；不冒充物理按键或像素验收"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--journal-report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.report.read_text(encoding="utf-8-sig"), args.journal_report.read_text(encoding="utf-8-sig"))
    if args.output:
        args.output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
