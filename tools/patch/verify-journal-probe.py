"""核查真实资料页面采集，明确区分来源、导航、缓存命中和实际控件翻译。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path


def decoded(value: str) -> str:
    return base64.b64decode(value, validate=True).decode("utf-8")


def analyze(path: Path, resource_path: Path) -> dict:
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line]
    required_documents = {"observable_hamletdiary", "observable_poldesk"}
    expected_navigation = {"hud", "journal", "timeline", "log"} | required_documents
    navigation = {row[1]: row[-1] == "True" for row in rows if row[0] == "NAVIGATION"}
    owners = {row[1]: dict(value.split("=", 1) for value in row[2:]) for row in rows if row[0] == "NAV_OWNER"}
    tabs = {row[1] for row in rows if row[0] == "TAB"}
    documents = {row[1]: decoded(row[2]) for row in rows if row[0] == "DOCUMENT_SOURCE"}
    resources = json.loads(resource_path.read_text(encoding="utf-8-sig"))
    expected_sources = {
        row["origin"]["record_id"]: row["source_sha256"]
        for row in resources
        if row.get("origin", {}).get("asset") == "closeups"
        and row["origin"].get("field") == "text"
        and row["origin"].get("record_id") in required_documents
    }
    checks = {
        "collection_finished": ["STATUS", "COLLECTED"] in rows and not any(row[0] == "FAILURE" for row in rows),
        "save_guard_active": ["SAVE_WRITE_GUARD_ACTIVE", "True"] in rows,
        "all_real_navigation_confirmed": all(navigation.get(phase) for phase in expected_navigation),
        "real_log_overlay_owned": navigation.get("log") is True and owners.get("log", {}).get("overlay") == "True",
        "all_journal_tabs_activated": tabs == {"CharactersTab", "HearsayTab", "LeadsTab"},
        "real_document_sources_match": all(
            key in documents
            and hashlib.sha256(documents[key].encode()).hexdigest() == expected_sources.get(key)
            for key in required_documents
        ),
    }
    api_rows = []
    for row in rows:
        if row[0] != "API":
            continue
        source, target, displayed = decoded(row[3]), decoded(row[5]), decoded(row[6])
        api_rows.append({
            "phase": row[1], "key": row[2], "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "source_length": len(source), "found": row[4] == "True",
            "display_matches": row[4] == "True" and bool(target) and target == displayed,
            "reported_display_matches": row[7] == "True",
            "display_length": len(displayed), "target_length": len(target),
            "source_base64": row[3], "target_base64": row[5], "display_base64": row[6],
            "display_contract": row[2] != "resource_body",
        })
    checks["api_reported_matches_consistent"] = all(
        item["display_matches"] == item["reported_display_matches"] for item in api_rows
    )
    originals = {
        (row[1], row[3]): row[5] for row in rows if row[0] == "TEXT" and row[2] == "original"
    }
    initial_texts = {
        (row[1], row[3]): row[5] for row in rows if row[0] == "TEXT" and row[2] == "translated"
    }
    restored_texts = {
        (row[1], row[3]): row[5] for row in rows if row[0] == "TEXT" and row[2] == "restored"
    }
    control_rows = [row for row in rows if row[0] == "CONTROL"]
    required_roles = {
        "hud.time", "hud.room", "characters.name", "characters.body", "leads.title", "leads.body",
        "rumors.title", "rumors.body", "timeline.detail", "log.entry",
    }
    control_results = []
    for row in control_rows:
        phase, role, key = row[1:4]
        original = originals.get((phase, key))
        initial = initial_texts.get((phase, key))
        restored = restored_texts.get((phase, key))
        matched_api = [item for item in api_rows if item["phase"] == phase and item["key"] == key]
        source = decoded(original) if original is not None else ""
        display = decoded(initial) if initial is not None else ""
        passed = (
            row[5] == "True" and bool(source) and bool(display)
            and re.search(r"[A-Za-z]", source) is not None
            and re.search(r"[\u3400-\u9fff]", display) is not None
            and source != display and restored == initial
            and any(item["found"] and item["display_matches"] and item["source_base64"] == original
                    and item["display_base64"] == initial for item in matched_api)
        )
        control_results.append({
            "phase": phase, "role": role, "component_id": key, "path_base64": row[4],
            "passed": passed, "original_base64": original, "translated_base64": initial,
            "restored_base64": restored,
            "reason": "真实同一组件原文命中离线API，实际中文等于缓存译文并通过F8恢复" if passed
                      else "未取得非空真实原文/中文、缓存与显示不符或F8往返未一致",
        })
    for role in sorted(required_roles):
        checks[role.replace(".", "_") + "_actual_translation"] = any(
            item["role"] == role and item["passed"] for item in control_results
        )
    critical_keys = {"builder:Body", "component_stringbuilder", "component_string_bool", "component_string"}
    critical = [row for row in api_rows if row["key"] in critical_keys and row["phase"] in required_documents]
    expected_pairs = {(phase, key) for phase in required_documents for key in critical_keys}
    checks["real_document_body_components_translated"] = {(row["phase"], row["key"]) for row in critical} == expected_pairs and all(
        row["found"] and row["display_matches"] and row["target_length"] > 0
        and re.search(r"[\u3400-\u9fff]", decoded(row["target_base64"])) is not None
        and decoded(row["source_base64"]) == ("<line-height=90%>" if row["key"] == "builder:Body" else "") + documents.get(row["phase"], "")
        for row in critical
    )
    bare_documents = [row for row in api_rows if row["key"] == "resource_body" and row["phase"] in required_documents]
    checks["real_document_bare_source_cache_exists"] = {row["phase"] for row in bare_documents} == required_documents and all(
        row["source_sha256"] == expected_sources.get(row["phase"]) and row["found"]
        and re.search(r"[\u3400-\u9fff]", decoded(row["target_base64"])) is not None
        for row in bare_documents
    )
    checks["document_body_f8_actual_translation"] = all(
        any(row["phase"] == phase and row["role"] == "document.body" and row["passed"] for row in control_results)
        for phase in required_documents
    )
    roundtrips = [row for row in rows if row[0] == "ROUNDTRIP"]
    checks["f8_roundtrip_matches"] = bool(roundtrips) and all(
        row[-1] == "True" and row[4] == row[5]
        and originals.get((row[1], row[2])) == row[3]
        and initial_texts.get((row[1], row[2])) == row[4]
        and restored_texts.get((row[1], row[2])) == row[5]
        for row in roundtrips
    )
    content = [
        {"phase": row[1], "mode": row[2], "active_tmp_count": int(row[3]), "nonempty_getter_count": int(row[4])}
        for row in rows if row[0] == "CONTENT"
    ]
    required_content_phases = {"hud", "CharactersTab", "HearsayTab", "LeadsTab", "timeline", "log"} | required_documents
    checks["all_required_pages_have_nonempty_actual_text"] = all(
        any(row["phase"] == phase and row["mode"] == "translated" and row["nonempty_getter_count"] > 0 for row in content)
        for phase in required_content_phases
    )
    clocks = {(row[1], row[2]): {"mode": int(row[3]), "value_base64": row[4]}
              for row in rows if row[0] == "CLOCK"}
    clock_results = []
    for phase in sorted(required_content_phases):
        before, after = clocks.get((phase, "before")), clocks.get((phase, "after"))
        stable = (before is not None and after is not None and before["mode"] == after["mode"] == 2
                  and bool(decoded(before["value_base64"])) and before["value_base64"] == after["value_base64"])
        clock_results.append({"phase": phase, "paused_and_stable": stable, "before": before, "after": after})
    checks["all_phase_clocks_really_paused_and_stable"] = all(row["paused_and_stable"] for row in clock_results)
    checks["all_requested_phases_available"] = not any(row[0] == "UNAVAILABLE" for row in rows)
    counters = {(row[1], row[2], row[3]): int(row[4]) for row in rows if row[0] == "PREFIX_COUNT"}
    prefix_deltas = []
    for (phase, moment, name), before in counters.items():
        if not moment.endswith("_before"):
            continue
        entry = moment.removesuffix("_before")
        after = counters.get((phase, entry + "_after", name))
        prefix_deltas.append({"phase": phase, "entry": entry, "field": name, "before": before,
                              "after": after, "delta": None if after is None else after - before})
    findings = [
        row for row in api_rows if row["source_length"] > 0
        and (not row["found"] or (row["display_contract"] and not row["display_matches"]))
    ]
    return {
        "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "checks": checks,
        "passed": all(checks.values()), "cache_vs_display_findings": findings,
        "document_api": critical, "content": content,
        "controls": control_results,
        "clocks": clock_results,
        "prefix_deltas": prefix_deltas,
        "prefix_counters_unavailable": [row[1:] for row in rows if row[0] == "PREFIX_COUNTER_UNAVAILABLE"],
        "uncovered_roles": sorted(required_roles - {item["role"] for item in control_results}),
        "unavailable": [row[1:] for row in rows if row[0] == "UNAVAILABLE"],
        "failures_base64": [row[1] for row in rows if row[0] == "FAILURE"],
        "limitations": [
            "报告记录真实页面组件和真实资源，但不验证像素、不声称搜寻物件或完整游玩E2E。",
            "页面有激活TMP组件但getter为空时只作为故障证据，不能推定有可见正文。",
            "F8往返相等不能单独证明显示中文，需同时核对缓存命中与组件实际文本。",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-translated", action="store_true")
    parser.add_argument("--resources", type=Path, default=Path(__file__).resolve().parents[2] / "analysis/ui-audit/resource-strings.json")
    args = parser.parse_args()
    result = analyze(args.report, args.resources)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({"checks": result["checks"], "passed": result["passed"], "findings": len(result["cache_vs_display_findings"])}))
    structural = ["collection_finished", "save_guard_active", "all_real_navigation_confirmed", "all_journal_tabs_activated", "real_document_sources_match"]
    if not all(result["checks"][key] for key in structural) or (args.require_translated and not result["passed"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
