"""核对人物资源重放的真实头像、组件、完整正文和 F8；不称剧情解锁。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path


def dec(value):
    return base64.b64decode(value, validate=True).decode("utf-8")


def analyze(report, cases_bytes, journal, minimum_actors=14):
    checks = {key: False for key in ("schema_and_frozen_input", "real_portraits_and_guards",
        "complete_available_cases", "exact_source_and_translation", "real_cache", "original_display_restored",
        "unavailable_scope_explicit")}
    available, unavailable = [], []
    try:
        rows = [line.split("\t") for line in report.splitlines() if line]
        widths = {"SCHEMA": 2, "SCOPE": 2, "INPUT_SHA256": 2, "EXPECTED": 5, "CONTROL": 6,
                  "SOURCE": 5, "TEXT": 8, "API": 5, "RESTORE": 10, "ACTOR_STATUS": 3,
                  "UNAVAILABLE": 4, "STATUS": 2}
        expected = {}
        for line in cases_bytes.decode("utf-8-sig").splitlines():
            identifier, source, target, actor = line.split("\t")
            if identifier in expected or not identifier or not actor:
                raise ValueError("重放用例 ID 重复或为空")
            expected[identifier] = (actor, dec(source), dec(target))
        checks["schema_and_frozen_input"] = (
            bool(expected) and all(r[0] in widths and len(r) == widths[r[0]] for r in rows)
            and [r for r in rows if r[0] == "SCHEMA"] == [["SCHEMA", "1"]]
            and [r for r in rows if r[0] == "SCOPE"] == [["SCOPE", "real_resource_component_replay"]]
            and [r for r in rows if r[0] == "INPUT_SHA256"] == [["INPUT_SHA256", hashlib.sha256(cases_bytes).hexdigest()]]
            and [r for r in rows if r[0] == "STATUS"] == [["STATUS", "COLLECTED"]])
        reported = [r for r in rows if r[0] == "EXPECTED"]
        checks["schema_and_frozen_input"] &= (len(reported) == len(expected)
            and {r[1]: (r[2], dec(r[3]), dec(r[4])) for r in reported} == expected)
        if not checks["schema_and_frozen_input"]:
            return {"passed": False, "checks": checks, "available_actors": [], "unavailable_cases": []}
        controls = [r for r in rows if r[0] == "CONTROL"]
        control_map = {r[1]: r for r in controls}
        actor_statuses = [r for r in rows if r[0] == "ACTOR_STATUS"]
        journal_controls = [r for r in (line.split("\t") for line in journal.splitlines())
                            if r[0] == "CONTROL" and len(r) == 6 and r[2] == "character.profile.body"]
        journal_control_map = {}
        for row in journal_controls:
            actor = row[1].removeprefix("character:")
            journal_control_map.setdefault(actor, set()).add((row[3], row[5]))
        available = sorted(control_map)
        checks["real_portraits_and_guards"] = (
            len(controls) == len(control_map) >= minimum_actors
            and all(r[2] != "0" and int(r[2]) != 0 and r[3:] == ["True"] * 3
                    and journal_control_map.get(r[1]) == {(r[2], "True")} for r in controls)
            and len(actor_statuses) == len(control_map)
            and {r[1] for r in actor_statuses} == set(control_map)
            and all(r[2] == "COLLECTED" for r in actor_statuses))
        selected = {key: value for key, value in expected.items() if value[0] in control_map}
        sources = [r for r in rows if r[0] == "SOURCE"]
        source_map = {r[1]: r for r in sources}
        texts = [r for r in rows if r[0] == "TEXT"]
        text_map = {(r[1], r[2]): r for r in texts}
        apis = [r for r in rows if r[0] == "API"]
        api_map = {r[1]: r for r in apis}
        checks["complete_available_cases"] = (
            len(sources) == len(source_map) == len(selected) and set(source_map) == set(selected)
            and len(texts) == len(text_map) == len(selected) * 3
            and set(text_map) == {(key, mode) for key in selected for mode in ("translated", "original", "restored")}
            and len(apis) == len(api_map) == len(selected) and set(api_map) == set(selected)
            and all(any(value[0] == actor for value in selected.values()) for actor in available))
        checks["exact_source_and_translation"] = bool(selected)
        checks["real_cache"] = bool(selected)
        for identifier, (actor, source, target) in selected.items():
            wrapped = "<line-height=90%>" + source
            current = source_map[identifier]
            checks["exact_source_and_translation"] &= (
                current[2] == actor and current[3] == control_map[actor][2]
                and dec(current[4]) == wrapped and target != wrapped)
            for mode in ("translated", "original", "restored"):
                item = text_map[(identifier, mode)]
                checks["exact_source_and_translation"] &= (
                    item[3] == current[3] and item[4] == "True" and dec(item[5]) == (wrapped if mode == "original" else target)
                    and dec(item[6]) == wrapped and item[7:] == ["False" if mode == "original" else "True"])
            api = api_map[identifier]
            checks["real_cache"] &= api[2] == "True" and dec(api[3]) == dec(api[4]) == target
        restores = [r for r in rows if r[0] == "RESTORE"]
        checks["original_display_restored"] = (
            len(restores) == len(control_map) and {r[1] for r in restores} == set(control_map)
            and all(r[2] == control_map[r[1]][2] and dec(r[3]) == dec(r[4]) and dec(r[5]) == dec(r[6])
                    and r[7:] == ["True"] * 3 for r in restores))
        unavailable = [r for r in rows if r[0] == "UNAVAILABLE"]
        missing = {key: value for key, value in expected.items() if value[0] not in control_map}
        checks["unavailable_scope_explicit"] = (
            len(unavailable) == len(missing) and {r[1] for r in unavailable} == set(missing)
            and all(r[2] == missing[r[1]][0] and r[3] == "no_frozen_portrait" for r in unavailable))
    except (ValueError, IndexError, KeyError, TypeError, UnicodeError):
        checks["schema_and_frozen_input"] = False
    return {"passed": all(checks.values()), "scope": "真实资源组件重放，未修改剧情获知条件", "checks": checks,
            "available_actors": available, "unavailable_cases": [r[1:3] for r in unavailable]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--journal-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.report.read_text(encoding="utf-8-sig"), args.cases.read_bytes(),
                     args.journal_report.read_text(encoding="utf-8-sig"))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
