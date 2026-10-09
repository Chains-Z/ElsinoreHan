"""核查真实资料页面采集，明确区分来源、导航、缓存命中和实际控件翻译。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
from pathlib import Path


def decoded(value: str) -> str:
    return base64.b64decode(value, validate=True).decode("utf-8")


def runtime_closeup_source(source: str) -> str:
    """严格复现Elsinore.dll CompilerPasses.doTextReplacement的9次顺序替换。"""
    for token in (" -- ", " --- ", " - ", "-- ", "--- ", " --", " ---", "--", "---"):
        source = source.replace(token, "—")
    return source


def runtime_closeup_target(source: str, target: str | None) -> str | None:
    """离线缓存保留真实源的边缘空白；构造完整目标，不裁剪实际显示。"""
    if target is None:
        return None
    leading = source[:len(source) - len(source.lstrip())]
    trailing = source[len(source.rstrip()):]
    return leading + target.strip() + trailing


def unapproved_english(text: str) -> list[str]:
    """只放行真实富文本标记和明确键名，正文残留英文须由人工核对后精确处理。"""
    text = re.sub(
        r"</?(?:alpha|align|allcaps|b|br|color|cspace|font|font-weight|i|indent|line-height|line-indent|link|lowercase|margin|mark|mspace|nobr|noparse|page|pos|rotate|s|size|space|sprite|style|sub|sup|u|uppercase|voffset|width)\b[^>]*>",
        "", text, flags=re.IGNORECASE,
    )
    text = html.unescape(text)
    keys = r"(?:F(?:[1-9]|1[0-2])|Esc|Escape|Enter|Return|Tab|Shift|Ctrl|Control|Alt|Space|Backspace|Delete|Insert|Home|End|PageUp|PageDown)"
    text = re.sub(r"\[(?:[A-Z]|" + keys + r")\]", "", text)
    text = re.sub(r"(?:Ctrl|Alt|Shift)(?:\+(?:Ctrl|Alt|Shift))*\+[A-Z]", "", text)
    text = re.sub(r"(?<![A-Za-z0-9])" + keys + r"(?![A-Za-z0-9])", "", text)
    return sorted(set(re.findall(r"[A-Za-z][A-Za-z0-9]*(?:['’][A-Za-z]+)*", text)))


def analyze(path: Path, resource_path: Path) -> dict:
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line]
    required_documents = {"observable_hamletdiary", "observable_poldesk", "observable_backerbook4"}
    expected_navigation = {"hud", "journal", "timeline", "log", "present"} | required_documents
    navigation = {row[1]: row[-1] == "True" for row in rows if row[0] == "NAVIGATION"}
    owners = {row[1]: dict(value.split("=", 1) for value in row[2:]) for row in rows if row[0] == "NAV_OWNER"}
    tabs = {row[1] for row in rows if row[0] == "TAB"}
    documents = {row[1]: decoded(row[2]) for row in rows if row[0] == "DOCUMENT_SOURCE"}
    resources = json.loads(resource_path.read_text(encoding="utf-8-sig"))
    closeup_resources = {
        row["origin"]["record_id"]: row
        for row in resources
        if row.get("origin", {}).get("asset") == "closeups"
        and row["origin"].get("field") == "text"
    }
    expected_runtime_sources = {key: runtime_closeup_source(row["source"]) for key, row in closeup_resources.items()}
    expected_sources = {key: hashlib.sha256(source.encode()).hexdigest() for key, source in expected_runtime_sources.items()}
    expected_targets = {
        key: runtime_closeup_target(expected_runtime_sources[key], row.get("target"))
        for key, row in closeup_resources.items()
    }
    checks = {
        "collection_finished": ["STATUS", "COLLECTED"] in rows and not any(row[0] == "FAILURE" for row in rows),
        "save_guard_active": ["SAVE_WRITE_GUARD_ACTIVE", "True"] in rows,
        "frozen_closeup_resource_hashes_valid": all(
            hashlib.sha256(row["source"].encode()).hexdigest() == row["source_sha256"]
            for row in closeup_resources.values()
        ),
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
    history_counts = [int(row[1]) for row in rows if row[0] == "HISTORY_COUNT"]
    entry_counts = [int(row[1]) for row in rows if row[0] == "LOG_ENTRIES_COUNT"]
    history_rows = [row for row in rows if row[0] == "HISTORY_SOURCE"]
    entry_rows = [row for row in rows if row[0] == "LOG_ENTRY"]
    history = {int(row[1]): row[2] for row in history_rows}
    entries = {int(row[1]): row for row in entry_rows}
    log_roundtrip_rows = [row for row in rows if row[0] == "LOG_ROUNDTRIP"]
    log_roundtrips = {int(row[1]): row for row in log_roundtrip_rows}
    count = history_counts[0] if len(history_counts) == 1 else 0
    expected_indices = set(range(count))
    complete_binding = (
        count > 0 and entry_counts == [count]
        and len(history_rows) == len(history) == len(entry_rows) == len(entries) == count
        and set(history) == set(entries) == expected_indices
        and len({row[2] for row in entry_rows}) == count
        and len(log_roundtrip_rows) == len(log_roundtrips) == count and set(log_roundtrips) == expected_indices
    )
    log_results = []
    for index in sorted(expected_indices):
        source_b64 = history.get(index)
        binding = entries.get(index)
        if source_b64 is None or binding is None:
            log_results.append({"index": index, "source_bound": False, "translated": False,
                                "original_exact": False, "restored_exact": False, "unapproved_english": []})
            continue
        source = decoded(source_b64)
        component = binding[2]
        initial = initial_texts.get(("log", component))
        original = originals.get(("log", component))
        restored = restored_texts.get(("log", component))
        actual = decoded(initial) if initial is not None else ""
        english = unapproved_english(actual)
        matched_api = [row for row in api_rows if row["phase"] == "log" and row["key"] == "history:" + str(index)]
        cache_matches = len(matched_api) == 1 and any(
            row["found"] and row["source_base64"] == source_b64 and row["target_base64"] == initial
            and row["display_base64"] == initial and row["display_matches"] for row in matched_api
        )
        source_bound = binding[4] == source_b64 and binding[5] == "True" and component != "0"
        trip = log_roundtrips.get(index)
        original_exact = (original is not None and original == source_b64 and trip is not None
                          and trip[2] == component and trip[3] == source_b64 and trip[4] == original and trip[7] == "True")
        restored_exact = (initial is not None and restored == initial and trip is not None
                          and trip[5] == initial and trip[6] == restored and trip[8] == "True")
        # HistoryText在已完成组后追加当前builder；它可能严格为空，仍逐索引核验同一控件F8。
        # 空源无需翻译缓存，但三个phase和激活时实际显示都必须严格为空，不能遮住漏译正文。
        empty_preserved = (source == "" and binding[6] == "" and initial == original == restored == ""
                           and original_exact and restored_exact)
        text_translated = bool(actual) and not english and (
            not unapproved_english(source) or (source != actual and re.search(r"[\u3400-\u9fff]", actual) is not None)
        )
        log_results.append({
            "index": index, "component_id": component, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "source_base64": source_b64, "original_base64": original, "translated_base64": initial,
            "restored_base64": restored, "source_bound": source_bound,
            "empty_source_preserved": empty_preserved,
            "whole_source_cache_matches": cache_matches, "translated": empty_preserved or (cache_matches and text_translated),
            "original_exact": original_exact, "restored_exact": restored_exact, "unapproved_english": english,
        })
    checks["log_all_real_history_indices_bound"] = complete_binding and all(row["source_bound"] for row in log_results)
    checks["log_all_entries_completely_translated"] = complete_binding and any(decoded(value) for value in history.values()) and all(row["translated"] for row in log_results)
    checks["log_all_entries_f8_original_exact"] = complete_binding and all(row["original_exact"] for row in log_results)
    checks["log_all_entries_f8_restored_exact"] = complete_binding and all(row["restored_exact"] for row in log_results)
    checks["log_no_unapproved_english"] = complete_binding and all(not row["unapproved_english"] for row in log_results)
    critical_keys = {"builder:Body", "component_stringbuilder", "component_string_bool", "component_string"}
    critical = [row for row in api_rows if row["key"] in critical_keys and row["phase"] in required_documents]
    expected_pairs = {(phase, key) for phase in required_documents for key in critical_keys}
    checks["real_document_body_components_translated"] = {(row["phase"], row["key"]) for row in critical} == expected_pairs and all(
        row["found"] and row["display_matches"] and row["target_length"] > 0
        and re.search(r"[\u3400-\u9fff]", decoded(row["target_base64"])) is not None
        and decoded(row["source_base64"]) == ("<line-height=90%>" if row["key"] == "builder:Body" else "") + documents.get(row["phase"], "")
        for row in critical
    )
    checks["real_document_cache_targets_complete"] = all(
        expected_targets.get(row["phase"]) is not None
        and decoded(row["target_base64"]) == ("<line-height=90%>" if row["key"] == "builder:Body" else "") + expected_targets[row["phase"]]
        for row in critical
    ) and {(row["phase"], row["key"]) for row in critical} == expected_pairs
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
    required_content_phases = {"hud", "CharactersTab", "HearsayTab", "LeadsTab", "timeline", "log", "present"} | required_documents
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
    batch_rows = [row for row in rows if row[0] == "CLOSEUP_BATCH"]
    batch_counts = [int(row[1]) for row in rows if row[0] == "CLOSEUP_BATCH_EXPECTED_COUNT"]
    batch_file_hashes = [row[1] for row in rows if row[0] == "CLOSEUP_IDS_FILE_SHA256"]
    batch_results = []
    for row in batch_rows:
        closeup_id = row[1]
        source, combined, display = decoded(row[2]), decoded(row[3]), decoded(row[4])
        known = closeup_resources.get(closeup_id)
        target = expected_targets.get(closeup_id)
        matched = [item for item in api_rows if item["phase"] == "batch:" + closeup_id and item["key"] == "builder:Body"]
        source_matches = known is not None and hashlib.sha256(source.encode()).hexdigest() == expected_sources[closeup_id]
        passed = (source_matches and combined == "<line-height=90%>" + source
                  and target is not None and display == "<line-height=90%>" + target
                  and len(matched) == 1 and matched[0]["found"] and matched[0]["display_matches"]
                  and matched[0]["source_base64"] == row[3] and matched[0]["display_base64"] == row[4])
        batch_results.append({"id": closeup_id, "passed": passed, "source_matches": source_matches,
                              "source_base64": row[2], "combined_base64": row[3], "display_base64": row[4]})
    checks["all_closeup_frozen_ids_consumed"] = (
        batch_counts == [len(closeup_resources)] and len(batch_rows) == len(closeup_resources)
        and {row[1] for row in batch_rows} == set(closeup_resources)
        and len(batch_file_hashes) == 1 and re.fullmatch(r"[a-f0-9]{64}", batch_file_hashes[0]) is not None
    )
    checks["all_closeup_complete_real_targets_displayed"] = checks["all_closeup_frozen_ids_consumed"] and all(row["passed"] for row in batch_results)
    geometry_rows = [row for row in rows if row[0] == "CHARACTER_GEOMETRY"]
    layout_rows = [row for row in rows if row[0] == "CHARACTER_LAYOUT"]
    layout_counts = [int(row[1]) for row in rows if row[0] == "CHARACTER_LAYOUT_EXPECTED_COUNT"]
    layouts = []
    for row in layout_rows:
        actor = row[1]
        metrics = {item[2]: item for item in geometry_rows if item[1] == actor}
        title, subtitle = metrics.get("title"), metrics.get("subtitle")
        overlap = True
        if title is not None and subtitle is not None:
            ax, ay, aw, ah = map(float, title[8:12])
            bx, by, bw, bh = map(float, subtitle[8:12])
            overlap = (aw > 0 and ah > 0 and bw > 0 and bh > 0
                       and min(ax + aw, bx + bw) - max(ax, bx) > 0.5
                       and min(ay + ah, by + bh) - max(ay, by) > 0.5)
        passed = (title is not None and subtitle is not None and bool(decoded(title[3]))
                  and int(title[4]) == 1 and float(title[5]) > 0 and title[12] == "False"
                  and float(title[10]) > 0 and float(title[11]) > 0
                  and not overlap and row[2] == "False")
        layouts.append({"character": actor, "passed": passed, "overlap": overlap,
                        "title": title[3:] if title is not None else None, "subtitle": subtitle[3:] if subtitle is not None else None})
    checks["all_known_characters_layout_consumed"] = len(layout_counts) == 1 and layout_counts[0] > 0 and len(layout_rows) == layout_counts[0] and len({row[1] for row in layout_rows}) == layout_counts[0]
    checks["all_known_character_titles_fit_without_overlap"] = checks["all_known_characters_layout_consumed"] and all(row["passed"] for row in layouts)
    preview_sources = [row[1] for row in rows if row[0] == "PRESENT_PREVIEW_SOURCE"]
    preview_origins = [row for row in rows if row[0] == "PRESENT_PREVIEW_ORIGIN"]
    preview_api = [row for row in api_rows if row["phase"] == "present" and row["key"] == "builder:PresentPreviewText"]
    preview_controls = [row for row in control_results if row["phase"] == "present" and row["role"] == "present.preview"]
    project_root = resource_path.parents[2]
    notification_path = resource_path.with_name("notification-source-audit.json")
    notification = json.loads(notification_path.read_text(encoding="utf-8-sig"))
    notification_tests_path = project_root / "translation/supplemental/notification-ui-tests.json"
    notification_tests = json.loads(notification_tests_path.read_text(encoding="utf-8-sig"))
    share_sources = notification["share_display_sources"]
    source_by_hash = {row["source_sha256"]: row["source"] for row in share_sources}
    whitelist_valid = (len(share_sources) == notification["share_unique_sources_count"] == 314
                       and len(source_by_hash) == 314 and all(
                           hashlib.sha256(row["source"].encode()).hexdigest() == row["source_sha256"]
                           for row in share_sources))
    quoted_targets = {
        '"' + runtime_closeup_source(row["source"][1:-1]) + '"': row["target"]
        for row in notification_tests
        if row["id"].startswith("present-quoted-firstline-") and row["source"].startswith('"') and row["source"].endswith('"')
    }
    selected_source = decoded(preview_sources[0]) if len(preview_sources) == 1 else ""
    origin = preview_origins[0] if len(preview_origins) == 1 and len(preview_origins[0]) == 7 else None
    matched_scenes = []
    if origin is not None:
        information_id, target_id, scene_id, firstline = map(decoded, origin[1:5])
        matched_scenes = [row for row in notification["share_first_dialogue_audit"]
                          if row["scene_id"] == scene_id and information_id in row["information_ids"]
                          and row["source_sha256"] in source_by_hash
                          and runtime_closeup_source(source_by_hash[row["source_sha256"]]) == firstline]
        origin_valid = (bool(target_id) and bool(firstline) and selected_source == '"' + firstline + '"'
                        and origin[5] == hashlib.sha256(firstline.encode()).hexdigest()
                        and origin[6] == hashlib.sha256(selected_source.encode()).hexdigest()
                        and bool(matched_scenes))
    else:
        origin_valid = False
    checks["real_information_preview_source_whitelisted"] = whitelist_valid and origin_valid and selected_source in quoted_targets
    checks["real_quoted_information_preview_translated"] = (
        checks["real_information_preview_source_whitelisted"] and len(preview_sources) == len(preview_api) == 1
        and preview_api[0]["source_base64"] == preview_sources[0] and preview_api[0]["found"] and preview_api[0]["display_matches"]
        and decoded(preview_api[0]["target_base64"]) == quoted_targets[selected_source]
        and not unapproved_english(decoded(preview_api[0]["display_base64"]))
        and any(row["passed"] and row["original_base64"] == preview_sources[0] for row in preview_controls)
    )
    component_evidence = notification.get("actual_component_verification", {})
    suite = component_evidence.get("notification_suite", {})
    artifact_hashes = component_evidence.get("artifact_sha256", {})
    danger_cases = [row for row in notification_tests if row["source"] in {
        '"Someone is after my life."',
        '"Someone is after my life, and I\'ve experienced things I cannot explain."',
    }]
    checks["danger_preview_existing_real_consumer_coverage"] = (
        suite.get("actual_recursive_xunity_consumer_passed") is True and suite.get("count") == len(notification_tests) == 596
        and len(danger_cases) == 2 and all(not unapproved_english(row["target"]) and row["target"] != row["source"] for row in danger_cases)
        and all(hashlib.sha256((project_root / file).read_bytes()).hexdigest() == artifact_hashes.get(file)
                for file in ("translation/supplemental/notification-ui-tests.json", "translation/supplemental/notification-ui-rules.json"))
    )
    checks["information_preview_not_submitted"] = [row[1] for row in rows if row[0] == "PRESENT_SUBMIT_BLOCKED_COUNT"] == ["0"]
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
        "document_source_contracts": [
            {"id": key, "resource_sha256": closeup_resources[key]["source_sha256"],
             "expected_runtime_sha256": expected_sources[key],
             "actual_runtime_sha256": hashlib.sha256(documents[key].encode()).hexdigest() if key in documents else None,
             "resource_length": len(closeup_resources[key]["source"]),
             "expected_runtime_length": len(expected_runtime_sources[key]),
             "expected_target_base64": base64.b64encode(expected_targets[key].encode()).decode() if expected_targets[key] is not None else None}
            for key in sorted(required_documents)
        ],
        "controls": control_results,
        "log_entries": log_results,
        "closeup_batch": batch_results,
        "information_preview": {
            "source_base64": preview_sources[0] if len(preview_sources) == 1 else None,
            "origin": origin[1:] if origin is not None else None,
            "matched_real_scenes": matched_scenes,
            "whitelist_sha256": hashlib.sha256(notification_path.read_bytes()).hexdigest(),
            "danger_scene_in_this_ui_run": "Someone is after my life" in selected_source,
            "danger_consumer_cases": [row["id"] for row in danger_cases],
        },
        "character_layouts": layouts,
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
            "分享UI消费当前实际已获得信息；指定Someone危险首句由既有596项真实消费者测试覆盖，未据此宣称本次UI进入该危险场景。",
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
