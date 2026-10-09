"""验证真实地图确认框、F8三态和取消保护；不把组件集成称为物理输入或移动E2E。"""

import argparse
import base64
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def decode(value):
    return base64.b64decode(value, validate=True).decode("utf-8")


def analyze(text, expected):
    """缺失、失活、漏译、提前关闭及取消导致状态改变都不能记录为通过。"""
    rows = [line.split("\t") for line in text.splitlines() if line]
    by_kind = {}
    for row in rows:
        by_kind.setdefault(row[0], []).append(row)
    checks = {
        "schema_valid": by_kind.get("SCHEMA") == [["SCHEMA", "1"]],
        "physical_and_save_guards_active": by_kind.get("SAVE_GUARD_ACTIVE") == [["SAVE_GUARD_ACTIVE", "True"]]
        and by_kind.get("PHYSICAL_INPUT_GUARD_ACTIVE") == [["PHYSICAL_INPUT_GUARD_ACTIVE", "True"]],
        "actual_map_ready": by_kind.get("NAVIGATION") == [["NAVIGATION", "map", "True", "True"]],
        "upper_hallway_covered": False,
        "case_sources_match_real_whitelist": True,
        "cache_matches_frozen": True,
        "all_three_active_modes": True,
        "same_component_and_source": True,
        "english_original_exact": True,
        "translated_restored_exact": True,
        "all_button_clicks_consumed": bool(by_kind.get("CLICK")) and all(len(row) == 4 and row[3] == "True" for row in by_kind.get("CLICK", [])),
        "cancelled_only_with_no": True,
        "player_location_unchanged": False,
        "paused_clock_unchanged": False,
        "hamlet_coverage_recorded": False,
        "report_complete": by_kind.get("STATUS") == [["STATUS", "COLLECTED"]] and not by_kind.get("FAILURE"),
    }
    cases = by_kind.get("CASE", [])
    identifiers = [row[1] for row in cases if len(row) == 5]
    checks["schema_valid"] &= bool(cases) and len(identifiers) == len(cases) and len(set(identifiers)) == len(identifiers)
    details = []
    try:
        for case in cases:
            if len(case) != 5:
                continue
            identifier, kind, parameter, button_path = case[1], case[2], decode(case[3]), decode(case[4])
            source_rows = [row for row in by_kind.get("SOURCE", []) if len(row) == 3 and row[1] == identifier]
            api_rows = [row for row in by_kind.get("API", []) if len(row) == 4 and row[1] == identifier]
            samples = [row for row in by_kind.get("SAMPLE", []) if len(row) == 9 and row[1] == identifier]
            source = decode(source_rows[0][2]) if len(source_rows) == 1 else None
            frozen = expected.get(source)
            target = frozen.get("target") if isinstance(frozen, dict) else frozen
            checks["case_sources_match_real_whitelist"] &= bool(button_path) and kind in ("room", "character") and source == "Go to " + parameter + "?" and target is not None
            if isinstance(frozen, dict):
                checks["case_sources_match_real_whitelist"] &= frozen.get("parameter_kind") == kind and frozen.get("parameter_source") == parameter
            checks["upper_hallway_covered"] |= identifier == "upper-hallway" and kind == "room" and parameter == "Upper Hallway" and source == "Go to Upper Hallway?"
            checks["cache_matches_frozen"] &= len(api_rows) == 1 and api_rows[0][2] == "True" and decode(api_rows[0][3]) == target
            modes = {row[2]: row for row in samples}
            checks["all_three_active_modes"] &= len(samples) == 3 and set(modes) == {"translated", "original", "restored"}
            checks["all_three_active_modes"] &= all(row[7] == "True" and row[8] == ("False" if row[2] == "original" else "True") for row in samples)
            checks["same_component_and_source"] &= len(samples) == 3 and len({row[3] for row in samples}) == 1 and all(row[3].lstrip("-").isdigit() and int(row[3]) != 0 for row in samples)
            checks["same_component_and_source"] &= len({row[4] for row in samples}) == 1 and all("/ConfirmMoveDialog/" in decode(row[4]) and decode(row[5]) == source for row in samples)
            checks["english_original_exact"] &= "original" in modes and decode(modes["original"][6]) == source
            checks["translated_restored_exact"] &= all(mode in modes and decode(modes[mode][6]) == target for mode in ("translated", "restored"))
            cancel = [row for row in by_kind.get("CANCEL", []) if row[1:2] == [identifier]]
            clicks = [row for row in by_kind.get("CLICK", []) if row[1:2] == [identifier]]
            no_clicks = [row for row in by_kind.get("CLICK", []) if row[1:2] == [identifier + ".no"]]
            checks["cancelled_only_with_no"] &= cancel == [["CANCEL", identifier, "1", "True", "True"]] and len(no_clicks) == len(clicks) == 1
            if samples and cancel:
                checks["cancelled_only_with_no"] &= rows.index(cancel[0]) > max(rows.index(row) for row in samples)
                checks["cancelled_only_with_no"] &= rows.index(no_clicks[0]) > max(rows.index(row) for row in samples) if no_clicks else False
            details.append({"case": identifier, "kind": kind, "parameter": parameter, "source": source, "target": target})
        positions = by_kind.get("POSITION", [])
        clocks = by_kind.get("CLOCK", [])
        checks["player_location_unchanged"] = len(positions) == 2 and positions[0][1] == "before" and positions[1][1] == "after" and all(len(row) == 6 for row in positions)
        if checks["player_location_unchanged"]:
            checks["player_location_unchanged"] &= bool(decode(positions[0][2])) and positions[0][2] == positions[1][2]
            before, after = ([float(value) for value in row[3:]] for row in positions)
            checks["player_location_unchanged"] &= all(math.isfinite(a) and math.isfinite(b) and abs(a - b) < 0.0001 for a, b in zip(before, after))
        checks["paused_clock_unchanged"] = len(clocks) == 2 and all(len(row) == 4 and row[2] == "2" for row in clocks) and [row[1] for row in clocks] == ["before", "after"]
        if checks["paused_clock_unchanged"]:
            values = [float(row[3]) for row in clocks]
            checks["paused_clock_unchanged"] &= all(math.isfinite(value) for value in values) and abs(values[0] - values[1]) < 0.0001
        allowed_clicks = {"floor"} | set(identifiers) | {identifier + ".no" for identifier in identifiers}
        checks["cancelled_only_with_no"] &= all(len(row) == 4 and row[1] in allowed_clicks for row in by_kind.get("CLICK", []))
        for tag, width in (("CASE", 5), ("SOURCE", 3), ("API", 4), ("SAMPLE", 9), ("CANCEL", 5), ("POSITION", 6), ("CLOCK", 4)):
            checks["schema_valid"] &= all(len(row) == width for row in by_kind.get(tag, []))
        checks["schema_valid"] &= all(row[1] in identifiers for tag in ("SOURCE", "API", "SAMPLE", "CANCEL") for row in by_kind.get(tag, []) if len(row) > 1)
        hamlet = [case for case in details if case["case"] == "hamlet"]
        unavailable_hamlet = [row for row in by_kind.get("UNAVAILABLE", []) if len(row) == 3 and row[1] == "hamlet" and decode(row[2])]
        checks["hamlet_coverage_recorded"] = (len(hamlet) == 1 and not unavailable_hamlet
                                             and hamlet[0]["kind"] == "character" and hamlet[0]["parameter"] == "Hamlet") or (not hamlet and len(unavailable_hamlet) == 1)
    except (ValueError, UnicodeError, IndexError, TypeError):
        checks["schema_valid"] = False
    return {"passed": all(checks.values()), "checks": checks, "cases": details,
            "hamlet_covered": any(case.get("case") == "hamlet" for case in details),
            "unavailable": [row[1:] for row in by_kind.get("UNAVAILABLE", [])],
            "limitations": ["真实组件事件集成，未注入物理按键、不确认移动、不验收像素"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--cases", type=Path, default=ROOT / "translation/supplemental/map-ui-tests.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    expected = {row["source"]: row for row in json.loads(args.cases.read_text(encoding="utf-8")) if row["target"] is not None}
    result = analyze(args.report.read_text(encoding="utf-8-sig"), expected)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
