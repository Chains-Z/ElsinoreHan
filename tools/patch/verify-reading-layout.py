"""核验真实TMP日志姓名重放及逐头像人物介绍的F8位置报告。"""

import argparse
import base64
import json
import math
from pathlib import Path


def decode(value):
    return base64.b64decode(value, validate=True).decode("utf-8")


def analyze_speakers(report, cases):
    expected = {row[0]: (decode(row[1]), decode(row[2])) for row in (line.split("\t") for line in cases.splitlines() if line)}
    rows = [line.split("\t") for line in report.splitlines() if line]
    checks = {key: False for key in ("complete", "text_exact", "font_unchanged", "labels_clear_of_body", "same_component_roundtrip")}
    try:
        samples = [row for row in rows if row[0] == "SAMPLE"]
        keyed = {(row[1], row[2], row[3]): row for row in samples}
        wanted = {(identifier, width, phase) for identifier in expected for width in ("1", "0.72") for phase in ("translated", "original", "restored")}
        checks["complete"] = (rows[0] == ["SCHEMA", "1"] and rows[-1] == ["STATUS", "COLLECTED"]
            and len(samples) == len(keyed) == len(wanted) and set(keyed) == wanted and all(len(row) == 13 for row in samples))
        checks["text_exact"] = all(decode(row[12]) == expected[row[1]][row[3] != "original"] for row in samples)
        checks["font_unchanged"] = all(float(row[5]) == float(row[6]) > 0 for row in samples)
        checks["labels_clear_of_body"] = bool(samples) and all(all(math.isfinite(float(row[i])) for i in range(4, 9))
            and row[9] == row[10] and float(row[8]) - float(row[7]) >= float(row[6]) * 0.15 for row in samples)
        checks["same_component_roundtrip"] = all(len({keyed[(identifier, width, phase)][11] for phase in ("translated", "original", "restored")}) == 1
            for identifier in expected for width in ("1", "0.72"))
        minimum_gap = min(float(row[8]) - float(row[7]) for row in samples)
    except (ValueError, KeyError, IndexError, TypeError):
        checks["complete"] = False
        minimum_gap = None
    return {"passed": all(checks.values()), "checks": checks, "minimum_name_body_gap_ui": minimum_gap}


def analyze_biographies(report, journal):
    rows = [line.split("\t") for line in report.splitlines() if line]
    journal_rows = [line.split("\t") for line in journal.splitlines() if line]
    sources = {row[1].split(":", 1)[1]: decode(row[2]) for row in journal_rows if row[0] == "BUILDER" and row[1].startswith("character:")}
    checks = {key: False for key in ("complete_all_portraits", "source_and_text_exact", "fresh_biography_anchor", "same_paragraph_and_component", "position_restored_or_physically_clamped", "bottom_retained", "manual_scroll_not_pinned")}
    clamped = []
    try:
        samples = [row for row in rows if row[0] == "SAMPLE"]
        keyed = {(row[1], row[2], row[3], row[4]): row for row in samples}
        wanted = {(actor, name, leg, phase) for actor in sources for name in ("middle", "bottom", "manual-away") for leg in ("0", "1") for phase in ("before", "after")}
        checks["complete_all_portraits"] = (bool(sources) and rows[0] == ["SCHEMA", "1"] and rows[-1] == ["STATUS", "COLLECTED"]
            and len(samples) == len(keyed) == len(wanted) and set(keyed) == wanted and all(len(row) == 21 for row in samples))
        if not checks["complete_all_portraits"]:
            return {"passed": False, "checks": checks, "actors": sorted(sources), "boundary_clamps": []}
        for key in checks:
            checks[key] = True
        for actor in sources:
            for name in ("middle", "bottom", "manual-away"):
                for leg in ("0", "1"):
                    before, after = (keyed[(actor, name, leg, stage)] for stage in ("before", "after"))
                    for row in (before, after):
                        translated = (leg == "0") == (row[4] == "before")
                        checks["source_and_text_exact"] &= decode(row[17]) == decode(row[20]) == sources[actor] and decode(row[19]) == decode(row[18] if translated else row[17])
                    checks["fresh_biography_anchor"] &= before[7] == after[7] == "True" and int(after[6]) > int(before[6]) and before[12] == "captured"
                    checks["same_paragraph_and_component"] &= before[5] == after[5] and before[8] == after[8]
                    finite = all(math.isfinite(float(row[i])) for row in (before, after) for i in (9, 11, 13, 15, 16))
                    boundary = float(after[15]) <= 0.0001 or float(after[15]) >= 0.9999
                    restored = after[12] == "restored" and float(after[13]) <= 1
                    clamped_ok = after[12] == "boundary-clamped" and boundary
                    bottom = after[12] == "bottom-restored" and abs(float(after[15])) * max(0, float(after[16])) <= 1
                    measured_error = abs(float(after[11]) - float(before[9]))
                    consistent = bottom or abs(measured_error - float(after[13])) <= 0.05
                    checks["position_restored_or_physically_clamped"] &= finite and consistent and before[10] == after[10] == "True" and (restored or clamped_ok or bottom)
                    if before[14] == "True":
                        checks["bottom_retained"] &= after[14] == "True" and bottom
                    if name == "manual-away" and leg == "0" and float(before[16]) > 4:
                        checks["manual_scroll_not_pinned"] &= abs(float(before[15]) - 0.35) <= 0.0001 and before[14] == "False"
                    if clamped_ok:
                        clamped.append({"actor": actor, "case": name, "leg": leg, "error_ui": float(after[13])})
    except (ValueError, TypeError, IndexError, KeyError):
        checks["complete_all_portraits"] = False
    return {"passed": all(checks.values()), "checks": checks, "actors": sorted(sources), "boundary_clamps": clamped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--speaker-cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    read = lambda name: (args.directory / name).read_text(encoding="utf-8-sig")
    result = {"speakers": analyze_speakers(read("log-speaker-layout.tsv"), args.speaker_cases.read_text(encoding="utf-8-sig")),
              "biographies": analyze_biographies(read("biography-scroll.tsv"), read("journal-ui.txt")),
              "test_level": "真实头像、日志预制体及TMP几何集成；非物理按键、像素或完整剧情E2E"}
    result["passed"] = result["speakers"]["passed"] and result["biographies"]["passed"]
    args.output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"passed": result["passed"], "speaker_checks": result["speakers"]["checks"],
        "minimum_name_body_gap_ui": result["speakers"]["minimum_name_body_gap_ui"],
        "biography_checks": result["biographies"]["checks"], "portrait_count": len(result["biographies"]["actors"]),
        "boundary_clamp_count": len(result["biographies"]["boundary_clamps"])}, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
