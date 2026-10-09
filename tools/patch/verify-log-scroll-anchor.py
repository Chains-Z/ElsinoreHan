"""核验真实日志控件与F8段落基线恢复；不将纯映射测试算作布局验收。"""

import argparse
import base64
import json
import math
from pathlib import Path


def dec(value):
    return base64.b64decode(value, validate=True).decode("utf-8")


def analyze(report, journal):
    checks = {name: False for name in (
        "schema_valid", "real_log_and_guards", "all_four_positions", "history_bound_to_journal",
        "short_long_real_history", "same_entry_and_paragraph", "fresh_official_toggle_completion",
        "active_real_mesh_coordinates", "baseline_restored_within_one_ui_unit", "f8_text_exact",
    )}
    details = []
    unavailable = []
    try:
        rows = [line.split("\t") for line in report.splitlines() if line]
        journal_rows = [line.split("\t") for line in journal.splitlines() if line]
        grouped = {}
        for row in rows:
            grouped.setdefault(row[0], []).append(row)
        widths = {"SCHEMA": 2, "SCOPE": 2, "SAVE_GUARD_ACTIVE": 2, "PHYSICAL_INPUT_GUARD_ACTIVE": 2,
                  "NAVIGATION": 4, "HISTORY_COUNT": 2, "HISTORY": 4, "CASE": 4, "SAMPLE": 17,
                  "STATUS": 2, "UNAVAILABLE": 3, "FAILURE": 2}
        checks["schema_valid"] = all(row[0] in widths and len(row) == widths[row[0]] for row in rows)
        if not checks["schema_valid"]:
            return {"passed": False, "checks": checks, "cases": [], "unavailable": []}
        checks["schema_valid"] &= grouped.get("SCHEMA") == [["SCHEMA", "1"]]
        checks["real_log_and_guards"] = (
            grouped.get("SAVE_GUARD_ACTIVE") == [["SAVE_GUARD_ACTIVE", "True"]]
            and grouped.get("PHYSICAL_INPUT_GUARD_ACTIVE") == [["PHYSICAL_INPUT_GUARD_ACTIVE", "True"]]
            and grouped.get("NAVIGATION") == [["NAVIGATION", "log", "True", "True"]]
            and grouped.get("STATUS") == [["STATUS", "COLLECTED"]]
            and not grouped.get("FAILURE") and not grouped.get("UNAVAILABLE"))
        history_rows = grouped.get("HISTORY", [])
        history = {int(row[1]): (row[2], dec(row[3])) for row in history_rows}
        journal_history_rows = [row for row in journal_rows if row[0] == "HISTORY_SOURCE"]
        journal_history = {int(row[1]): dec(row[2]) for row in journal_history_rows}
        journal_entry_rows = [row for row in journal_rows if row[0] == "LOG_ENTRY"]
        journal_entries = {int(row[1]): row[2] for row in journal_entry_rows}
        # 同页标题等控件也会进入 TEXT；只消费 LOG_ENTRY 明确声明的完整历史控件集合。
        journal_entry_ids = set(journal_entries.values())
        journal_target_rows = [row for row in journal_rows if row[:3] == ["TEXT", "log", "translated"]
                               and len(row) >= 4 and row[3] in journal_entry_ids]
        journal_targets = {row[3]: dec(row[5]) for row in journal_target_rows}
        counts = grouped.get("HISTORY_COUNT", [])
        checks["history_bound_to_journal"] = (
            len(counts) == 1 and int(counts[0][1]) > 0
            and len(history_rows) == len(history) == int(counts[0][1])
            and len(journal_history_rows) == len(journal_history) == len(journal_entry_rows) == len(journal_entries) == len(history)
            and set(history) == set(range(len(history))) == set(journal_history) == set(journal_entries)
            and len(journal_target_rows) == len(journal_targets) == len(history)
            and len({component for component, _ in history.values()}) == len(history)
            and all(component != "0" and source == journal_history[index] and component == journal_entries[index]
                    and component in journal_targets for index, (component, source) in history.items()))
        cases = grouped.get("CASE", [])
        names = [row[1] for row in cases]
        checks["all_four_positions"] = len(names) == 4 and set(names) == {"middle", "short", "long-upper", "long-lower"}
        nonempty = {index: len(source) for index, (_, source) in history.items() if source}
        case_map = {row[1]: row for row in cases}
        if checks["all_four_positions"] and nonempty:
            short = int(case_map["short"][2])
            long = int(case_map["long-upper"][2])
            checks["short_long_real_history"] = (
                short != long and short in nonempty and long in nonempty
                and nonempty[short] == min(nonempty.values()) and nonempty[long] == max(nonempty.values())
                and int(case_map["long-lower"][2]) == long
                and case_map["middle"][2:] == ["-1", "middle"]
                and case_map["short"][3] == "short" and all(case_map[name][3] == "long" for name in ("long-upper", "long-lower")))
        for name in ("same_entry_and_paragraph", "fresh_official_toggle_completion", "active_real_mesh_coordinates",
                     "baseline_restored_within_one_ui_unit", "f8_text_exact"):
            checks[name] = checks["all_four_positions"] and checks["history_bound_to_journal"]
        samples = grouped.get("SAMPLE", [])
        checks["all_four_positions"] &= len(samples) == 16 and all(row[1] in case_map for row in samples)
        for name in names:
            chosen = [row for row in samples if row[1] == name]
            by_mode = {(row[2], row[3]): row for row in chosen}
            complete = len(chosen) == len(by_mode) == 4 and set(by_mode) == {(mode, stage) for mode in ("original", "restored") for stage in ("before", "after")}
            checks["all_four_positions"] &= complete
            if not complete:
                continue
            for mode in ("original", "restored"):
                before, after = by_mode[(mode, "before")], by_mode[(mode, "after")]
                intended = int(case_map[name][2])
                index = int(before[4])
                checks["same_entry_and_paragraph"] &= (
                    before[4:7] == after[4:7] and index in history and before[5] == history[index][0]
                    and int(before[6]) >= 0 and (intended < 0 or index == intended))
                checks["fresh_official_toggle_completion"] &= (
                    int(after[16]) > int(before[16]) and before[10] == "captured" and after[10] == "restored"
                    and before[12] == ("True" if mode == "original" else "False")
                    and after[12] == ("False" if mode == "original" else "True"))
                coordinates = [float(row[col]) for row in (before, after) for col in (7, 9, 11)]
                finite = all(math.isfinite(value) for value in coordinates)
                checks["active_real_mesh_coordinates"] &= finite and all(row[8] == row[13] == "True" for row in (before, after))
                checks["baseline_restored_within_one_ui_unit"] &= finite and (
                    abs(float(before[7]) - float(before[9])) <= 1
                    and abs(float(before[7]) - float(after[7])) <= 1
                    and abs(float(before[7]) - float(after[9])) <= 1
                    and 0 <= float(after[11]) <= 1)
                source = history.get(index, (None, None))[1]
                target = journal_targets.get(before[5])
                checks["f8_text_exact"] &= (
                    bool(source) and bool(target) and source != target
                    and dec(before[14]) == dec(after[14]) == source
                    and dec(before[15]) == (target if mode == "original" else source)
                    and dec(after[15]) == (source if mode == "original" else target))
                details.append({"case": name, "leg": mode, "history_index": index, "component_id": before[5],
                                "paragraph": int(before[6]), "actual_ui_error": abs(float(before[7]) - float(after[9])),
                                "outcome": after[10]})
        long_positions = [row for row in samples if row[1] in {"long-upper", "long-lower"} and row[2:4] == ["original", "before"]]
        checks["short_long_real_history"] &= len(long_positions) == 2 and long_positions[0][6:8] != long_positions[1][6:8]
        unavailable = [row[1:] for row in grouped.get("UNAVAILABLE", [])]
    except (ValueError, IndexError, TypeError, UnicodeError, KeyError, OverflowError):
        checks["schema_valid"] = False
    return {"passed": all(checks.values()), "checks": checks, "cases": details, "unavailable": unavailable,
            "limitations": ["真实TMP几何与正式共享F8入口；未注入物理键盘、不验像素", "硬换行结构变化及布局边界限制不能算精确恢复通过"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--journal-report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.report.read_text(encoding="utf-8-sig"), args.journal_report.read_text(encoding="utf-8-sig"))
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
