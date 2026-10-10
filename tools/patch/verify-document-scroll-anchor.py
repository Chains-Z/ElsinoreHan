"""核对真实文档、官方F8路径与段落几何；不把比例相同当成位置恢复。"""

import argparse
import base64
import json
import math
from pathlib import Path


def dec(value):
    return base64.b64decode(value, validate=True).decode("utf-8")


def analyze(report, journal, expected_ids):
    checks = {name: False for name in (
        "schema", "real_documents_and_guards", "three_reading_positions", "fresh_f8_completion",
        "same_body_source_and_paragraph", "real_finite_geometry", "same_baseline_within_one_ui_unit",
        "exact_original_and_translation", "normal_scroll_still_works",
    )}
    details = []
    try:
        rows = [line.split("\t") for line in report.splitlines() if line]
        widths = {"SCHEMA": 2, "GUARDS": 5, "DOCUMENT": 5, "SAMPLE": 18,
                  "STATUS": 3, "FAILURE": 3, "MANUAL_SCROLL": 4}
        checks["schema"] = (all(r[0] in widths and len(r) == widths[r[0]] for r in rows)
                            and [r for r in rows if r[0] == "SCHEMA"] == [["SCHEMA", "1"]])
        if not checks["schema"]:
            return {"passed": False, "checks": checks, "cases": []}
        ids = set(expected_ids)
        documents = [r for r in rows if r[0] == "DOCUMENT"]
        doc_map = {r[1]: r for r in documents}
        guards = [r for r in rows if r[0] == "GUARDS"]
        statuses = [r for r in rows if r[0] == "STATUS"]
        journal_docs = [r for r in (line.split("\t") for line in journal.splitlines())
                        if r[0] == "CLOSEUP_BATCH" and r[1] in ids]
        journal_map = {r[1]: r for r in journal_docs}
        checks["real_documents_and_guards"] = (
            bool(ids) and len(documents) == len(doc_map) == len(ids) and set(doc_map) == ids
            and len(guards) == len(ids) and {r[1] for r in guards} == ids
            and all(r[2:] == ["True", "True", "True"] for r in guards)
            and len(statuses) == len(ids) and {r[1] for r in statuses} == ids
            and all(r[2] == "COLLECTED" for r in statuses) and not any(r[0] == "FAILURE" for r in rows)
            and len(journal_docs) == len(journal_map) == len(ids)
            and all(r[2] != "0" and dec(r[3]) == dec(journal_map[r[1]][3])
                    and dec(r[4]) == dec(journal_map[r[1]][4]) and dec(r[3]) != dec(r[4]) for r in documents))
        samples = [r for r in rows if r[0] == "SAMPLE"]
        checks["three_reading_positions"] = len(samples) == len(ids) * 12 and all(r[1] in ids for r in samples)
        for name in ("fresh_f8_completion", "same_body_source_and_paragraph", "real_finite_geometry",
                     "same_baseline_within_one_ui_unit", "exact_original_and_translation"):
            checks[name] = checks["real_documents_and_guards"]
        for identifier in sorted(ids):
            document = doc_map[identifier]
            positions = set()
            for position in (0.8, 0.5, 0.2):
                chosen = [r for r in samples if r[1] == identifier and float(r[2]) == position]
                pair_map = {(r[3], r[4]): r for r in chosen}
                complete = len(chosen) == len(pair_map) == 4 and set(pair_map) == {
                    (mode, stage) for mode in ("original", "restored") for stage in ("before", "after")}
                checks["three_reading_positions"] &= complete
                if not complete:
                    continue
                positions.add(pair_map[("original", "before")][6])
                for mode in ("original", "restored"):
                    before, after = pair_map[(mode, "before")], pair_map[(mode, "after")]
                    checks["fresh_f8_completion"] &= (int(after[15]) > int(before[15])
                        and before[10] == "captured" and after[10] == "restored"
                        and before[12] == ("True" if mode == "original" else "False")
                        and after[12] == ("False" if mode == "original" else "True"))
                    checks["same_body_source_and_paragraph"] &= (
                        before[5:7] == after[5:7] and before[5] == document[2] and int(before[6]) >= 0
                        and before[16] == after[16] == "True" and dec(before[17]) == dec(after[17]) == dec(document[3]))
                    numbers = [float(r[col]) for r in (before, after) for col in (7, 9, 11)]
                    finite = all(math.isfinite(value) for value in numbers)
                    checks["real_finite_geometry"] &= finite and all(r[8] == r[13] == "True" for r in (before, after))
                    error = abs(float(before[7]) - float(after[9]))
                    checks["same_baseline_within_one_ui_unit"] &= finite and error <= 1 and (
                        abs(float(before[7]) - float(before[9])) <= 1
                        and abs(float(before[7]) - float(after[7])) <= 1 and 0 <= float(after[11]) <= 1)
                    checks["exact_original_and_translation"] &= (
                        dec(before[14]) == dec(document[4] if mode == "original" else document[3])
                        and dec(after[14]) == dec(document[3] if mode == "original" else document[4]))
                    details.append({"document": identifier, "position": position, "leg": mode,
                                    "paragraph": int(before[6]), "ui_error": error, "outcome": after[10]})
            checks["three_reading_positions"] &= len(positions) >= 2
        manual = [r for r in rows if r[0] == "MANUAL_SCROLL"]
        checks["normal_scroll_still_works"] = (len(manual) == len(ids) and {r[1] for r in manual} == ids
            and all(math.isfinite(float(r[2])) and math.isfinite(float(r[3]))
                    and abs(float(r[2]) - float(r[3])) > 1 for r in manual))
    except (ValueError, IndexError, KeyError, TypeError, UnicodeError, OverflowError):
        checks["schema"] = False
    return {"passed": all(checks.values()), "checks": checks, "cases": details,
            "limits": ["真实文档与TMP几何的共享F8入口，未注入物理键盘或验像素",
                       "保护硬换行段落的基线；不保证长段内逐词位置相同"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--journal-report", type=Path, required=True)
    parser.add_argument("--ids", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.report.read_text(encoding="utf-8-sig"),
                     args.journal_report.read_text(encoding="utf-8-sig"), args.ids.split(";"))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
