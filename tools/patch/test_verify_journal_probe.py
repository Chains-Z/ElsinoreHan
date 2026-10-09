"""构造故障报告核查验收判定；使用冻结真实文档片段，不作为游戏E2E。"""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESOURCE_PATH = ROOT / "analysis/ui-audit/resource-strings.json"
SPEC = importlib.util.spec_from_file_location("verify_journal_probe", Path(__file__).with_name("verify-journal-probe.py"))
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def encoded(value):
    return base64.b64encode(value.encode()).decode()


class JournalVerificationTests(unittest.TestCase):
    def test_governed_resource_target_supports_outer_source_whitespace(self):
        change = {"source": "Playmaster", "source_sha256": hashlib.sha256(b"Playmaster").hexdigest(),
                  "previous_target": "剧团团长", "target": "戏剧大师", "origins": ["用户明确校订"]}
        self.assertEqual(VERIFY.governed_resource_target("\nPlaymaster\n", "剧团团长", [change]), "戏剧大师")
        for key, value in (("previous_target", "错误旧译文"), ("source_sha256", "0" * 64), ("origins", [])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                VERIFY.governed_resource_target("Playmaster", "剧团团长", [{**change, key: value}])

    def test_governed_resource_target_does_not_change_unrelated_source(self):
        change = {"source": "Other", "target": "不应套用"}
        self.assertEqual(VERIFY.governed_resource_target("Playmaster", "剧团团长", [change]), "剧团团长")

    def setUp(self):
        resources = json.loads(RESOURCE_PATH.read_text(encoding="utf-8-sig"))
        self.documents = {
            row["origin"]["record_id"]: (VERIFY.runtime_closeup_source(row["source"]),
                                           VERIFY.runtime_closeup_target(row["source"], VERIFY.governed_resource_target(row["source"], row["target"], VERIFY.resource_corrections())))
            for row in resources
            if row.get("origin", {}).get("asset") == "closeups"
            and row["origin"].get("field") == "text"
            and row["origin"].get("record_id") in {"observable_hamletdiary", "observable_poldesk", "observable_backerbook4"}
        }
        self.directory = tempfile.TemporaryDirectory(dir=ROOT / "runtime/build")
        self.addCleanup(self.directory.cleanup)
        self.report = Path(self.directory.name) / "journal-ui.txt"
        self.rows = [["STATUS", "COLLECTED"], ["SAVE_WRITE_GUARD_ACTIVE", "True"]]
        phases = ["hud", "journal", "timeline", "log", "present"] + list(self.documents)
        self.rows += [["NAVIGATION", phase, "真实页面字段", "True"] for phase in phases]
        self.rows.append(["NAV_OWNER", "log", "modal=False", "overlay=True"])
        self.rows += [["TAB", tab, str(index)] for index, tab in enumerate(["CharactersTab", "HearsayTab", "LeadsTab"])]
        self.rows += [["DOCUMENT_SOURCE", key, encoded(source)] for key, (source, _) in self.documents.items()]
        roles = {
            "hud": ["hud.time", "hud.room"], "CharactersTab": ["characters.name", "characters.body"],
            "LeadsTab": ["leads.title", "leads.body"], "HearsayTab": ["rumors.title", "rumors.body"],
            "timeline": ["timeline.detail"], "log": ["log.entry"],
            "observable_hamletdiary": ["document.body"], "observable_poldesk": ["document.body"],
            "observable_backerbook4": ["document.body"],
        }
        key = 100
        for phase, phase_roles in roles.items():
            # 此处只验证报告解析器，不把复用文档片段宣称为各业务页面的来源。
            source, target = self.documents.get(phase, self.documents["observable_poldesk"])
            if phase in self.documents:
                source, target = "<line-height=90%>" + source, "<line-height=90%>" + target
            for role in phase_roles:
                key += 1
                component = str(key)
                self.rows.append(["CONTROL", phase, role, component, encoded(role), "True"])
                for mode, value in [("translated", target), ("original", source), ("restored", target)]:
                    self.rows.append(["TEXT", phase, mode, component, encoded(role), encoded(value), "False", encoded(value)])
                self.rows.append(["API", phase, component, encoded(source), "True", encoded(target), encoded(target), "True"])
                self.rows.append(["ROUNDTRIP", phase, component, encoded(source), encoded(target), encoded(target), "True"])
            for mode in ["translated", "original", "restored"]:
                self.rows.append(["CONTENT", phase, mode, str(len(phase_roles)), str(len(phase_roles))])
            for moment in ["before", "after"]:
                self.rows.append(["CLOCK", phase, moment, "2", encoded("1234.5")])
        for phase, (source, target) in self.documents.items():
            self.rows.append(["API", phase, "resource_body", encoded(source), "True", encoded(target),
                              encoded("<line-height=90%>" + target), "False"])
            for name in ["builder:Body", "component_stringbuilder", "component_string_bool", "component_string"]:
                prefix = "<line-height=90%>" if name == "builder:Body" else ""
                self.rows.append(["API", phase, name, encoded(prefix + source), "True", encoded(prefix + target), encoded(prefix + target), "True"])
        first_id = self.control("log.entry")[3]
        second = next(row for row in resources if row.get("origin", {}).get("record_id") == "observable_hamletdiary"
                      and row["origin"].get("field") == "title")
        source, target = second["source"], second["target"]
        second_id = str(key + 1)
        self.rows.append(["CONTROL", "log", "log.entry", second_id, encoded("log.second"), "True"])
        for mode, value in [("translated", target), ("original", source), ("restored", target)]:
            self.rows.append(["TEXT", "log", mode, second_id, encoded("log.second"), encoded(value), "False", encoded(value)])
        self.rows.append(["API", "log", second_id, encoded(source), "True", encoded(target), encoded(target), "True"])
        self.rows.append(["ROUNDTRIP", "log", second_id, encoded(source), encoded(target), encoded(target), "True"])
        first_source, first_target = self.documents["observable_poldesk"]
        self.rows += [["HISTORY_COUNT", "2"], ["LOG_ENTRIES_COUNT", "2"]]
        for index, component, source, target in [(0, first_id, first_source, first_target), (1, second_id, source, target)]:
            self.rows.append(["HISTORY_SOURCE", str(index), encoded(source)])
            self.rows.append(["LOG_ENTRY", str(index), component, encoded("log." + str(index)), encoded(source), "True", encoded(target)])
            self.rows.append(["API", "log", "history:" + str(index), encoded(source), "True", encoded(target), encoded(target), "True"])
            self.rows.append(["LOG_ROUNDTRIP", str(index), component, encoded(source), encoded(source), encoded(target), encoded(target), "True", "True"])
        for row in self.rows:
            if row[0] == "CONTENT" and row[1] == "log":
                row[3], row[4] = "2", "2"
        all_closeups = [row for row in resources if row.get("origin", {}).get("asset") == "closeups" and row["origin"].get("field") == "text"]
        self.rows += [["CLOSEUP_IDS_FILE_SHA256", "a" * 64], ["CLOSEUP_BATCH_EXPECTED_COUNT", str(len(all_closeups))]]
        for row in all_closeups:
            closeup_id = row["origin"]["record_id"]
            source = VERIFY.runtime_closeup_source(row["source"])
            target = VERIFY.runtime_closeup_target(source, VERIFY.governed_resource_target(row["source"], row["target"], VERIFY.resource_corrections()))
            combined, rendered = "<line-height=90%>" + source, "<line-height=90%>" + target
            self.rows.append(["CLOSEUP_BATCH", closeup_id, encoded(source), encoded(combined), encoded(rendered), "False"])
            self.rows.append(["API", "batch:" + closeup_id, "builder:Body", encoded(combined), "True", encoded(rendered), encoded(rendered), "True"])
        self.rows.append(["CHARACTER_LAYOUT_EXPECTED_COUNT", "3"])
        profile = json.loads((ROOT / "translation/supplemental/hamlet-bio-alias.json").read_text(encoding="utf-8"))[0]
        profile_source, profile_target = "<line-height=90%>" + profile["source"], "<line-height=90%>" + profile["target"]
        for actor in ["ophelia", "brit", "hamlet"]:
            self.rows.append(["CHARACTER_GEOMETRY", actor, "title", encoded("真实冻结资料的标题"), "1", "24", "200", "40", "0", "50", "100", "20", "False"])
            self.rows.append(["CHARACTER_GEOMETRY", actor, "subtitle", encoded("副标题"), "1", "18", "200", "30", "0", "25", "110", "18", "False"])
            self.rows.append(["CHARACTER_LAYOUT", actor, "False"])
            self.rows.append(["API", "character:" + actor, "builder:DescriptionText", encoded(profile_source), "True", encoded(profile_target), encoded(profile_target), "True"])
        self.rows.append(["CONTROL", "character:hamlet", "character.profile.body", "301", encoded("hamlet.description"), "True"])
        for mode, value in [("translated", profile_target), ("original", profile_source), ("restored", profile_target)]:
            self.rows.append(["TEXT", "character:hamlet", mode, "301", encoded("hamlet.description"), encoded(value), "False", encoded(value)])
        self.rows.append(["API", "character:hamlet", "301", encoded(profile_source), "True", encoded(profile_target), encoded(profile_target), "True"])
        translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        preview = next(row for row in translations if row["source"] == "Someone is after my life.")
        source, target = '"' + preview["source"] + '"', '“' + preview["target"] + '”'
        notification = json.loads((ROOT / "analysis/ui-audit/notification-source-audit.json").read_text(encoding="utf-8-sig"))
        source_sha = hashlib.sha256(preview["source"].encode()).hexdigest()
        origin = next(row for row in notification["share_first_dialogue_audit"] if row["source_sha256"] == source_sha)
        self.rows.append(["PRESENT_PREVIEW_SOURCE", encoded(source)])
        self.rows.append(["PRESENT_PREVIEW_ORIGIN", encoded(origin["information_ids"][0]), encoded("hamlet"),
                          encoded(origin["scene_id"]), encoded(preview["source"]), source_sha, hashlib.sha256(source.encode()).hexdigest()])
        self.rows.append(["PRESENT_SUBMIT_BLOCKED_COUNT", "0"])
        self.rows.append(["CONTROL", "present", "present.preview", "300", encoded("preview"), "True"])
        for mode, value in [("translated", target), ("original", source), ("restored", target)]:
            self.rows.append(["TEXT", "present", mode, "300", encoded("preview"), encoded(value), "False", encoded(value)])
            self.rows.append(["CONTENT", "present", mode, "1", "1"])
        for moment in ["before", "after"]:
            self.rows.append(["CLOCK", "present", moment, "2", encoded("1234.5")])
        self.rows.append(["API", "present", "300", encoded(source), "True", encoded(target), encoded(target), "True"])
        self.rows.append(["API", "present", "builder:PresentPreviewText", encoded(source), "True", encoded(target), encoded(target), "True"])
        self.rows.append(["ROUNDTRIP", "present", "300", encoded(source), encoded(target), encoded(target), "True"])

    def result(self):
        self.report.write_text("\n".join("\t".join(row) for row in self.rows) + "\n", encoding="utf-8")
        return VERIFY.analyze(self.report, RESOURCE_PATH)

    def control(self, role):
        return next(row for row in self.rows if row[0] == "CONTROL" and row[2] == role)

    def component_rows(self, role):
        control = self.control(role)
        return [row for row in self.rows if row[0] in {"TEXT", "API", "ROUNDTRIP"}
                and row[1] == control[1] and row[3 if row[0] == "TEXT" else 2] == control[3]]

    def replace_log_display(self, index, display, found=True):
        binding = next(row for row in self.rows if row[0] == "LOG_ENTRY" and row[1] == str(index))
        component, payload = binding[2], encoded(display)
        binding[6] = payload
        for row in self.rows:
            if row[0] == "TEXT" and row[1] == "log" and row[3] == component and row[2] in {"translated", "restored"}:
                row[5] = payload
            elif row[0] == "API" and row[1] == "log" and row[2] in {component, "history:" + str(index)}:
                row[4], row[5], row[6], row[7] = str(found), payload if found else "", payload, str(found)
            elif row[0] == "ROUNDTRIP" and row[1:3] == ["log", component]:
                row[4], row[5] = payload, payload
            elif row[0] == "LOG_ROUNDTRIP" and row[1] == str(index):
                row[5], row[6] = payload, payload

    def test_complete_consistent_report_passes(self):
        self.assertTrue(self.result()["passed"])

    def test_first_character_profile_cannot_represent_every_character(self):
        self.rows = [row for row in self.rows if not (
            row[0] == "API" and row[1].startswith("character:")
            and row[2] == "builder:DescriptionText" and row[1] != "character:ophelia")]
        self.assertFalse(self.result()["checks"]["all_known_character_profiles_translated"])

    def test_partial_chinese_hamlet_profile_is_rejected_even_with_api_hit(self):
        row = next(row for row in self.rows if row[:3] == ["API", "character:hamlet", "builder:DescriptionText"])
        row[5] = row[6] = encoded("哈姆雷特 recently lost his father.")
        self.assertFalse(self.result()["checks"]["all_known_character_profiles_translated"])

    def test_hamlet_profile_without_real_original_roundtrip_is_rejected(self):
        self.rows = [row for row in self.rows if not (row[:3] == ["TEXT", "character:hamlet", "original"])]
        self.assertFalse(self.result()["checks"]["hamlet_profile_f8_original_and_restored"])

    def add_empty_history_group(self):
        for row in self.rows:
            if row[0] in {"HISTORY_COUNT", "LOG_ENTRIES_COUNT"}:
                row[1] = "3"
        self.rows += [
            ["HISTORY_SOURCE", "2", ""],
            ["LOG_ENTRY", "2", "999", encoded("log.current_empty"), "", "True", ""],
            ["LOG_ROUNDTRIP", "2", "999", "", "", "", "", "True", "True"],
            ["API", "log", "history:2", "", "False", "", "", "False"],
        ]
        for mode in ("translated", "original", "restored"):
            self.rows.append(["TEXT", "log", mode, "999", encoded("log.current_empty"), "", "False", ""])

    def test_real_empty_current_history_group_is_exactly_preserved(self):
        self.add_empty_history_group()
        result = self.result()
        self.assertTrue(result["passed"])
        self.assertTrue(result["log_entries"][-1]["empty_source_preserved"])
        self.assertFalse(result["log_entries"][-1]["whole_source_cache_matches"])

    def test_empty_history_cannot_hide_nonempty_actual_display(self):
        self.add_empty_history_group()
        self.replace_log_display(2, "Untranslated history")
        result = self.result()
        self.assertFalse(result["checks"]["log_all_entries_completely_translated"])
        self.assertFalse(result["checks"]["log_no_unapproved_english"])

    def test_empty_history_still_requires_original_and_restored_snapshots(self):
        self.add_empty_history_group()
        self.rows = [row for row in self.rows if not (row[0] == "TEXT" and row[1:4] == ["log", "original", "999"])]
        result = self.result()
        self.assertFalse(result["checks"]["log_all_entries_f8_original_exact"])
        self.assertFalse(result["checks"]["log_all_entries_completely_translated"])

    def test_compiler_dash_replacements_follow_exact_order(self):
        self.assertEqual(VERIFY.runtime_closeup_source("a -- b --- c - d-- e--- f --g ---h--i---j"),
                         "a—b—c—d—e-—f—g—-h—i—-j")
        row = next(row for row in self.rows if row[0] == "DOCUMENT_SOURCE" and row[1] == "observable_backerbook4")
        self.assertEqual(len(VERIFY.decoded(row[2])), 4224)
        self.assertTrue(self.result()["checks"]["real_document_sources_match"])

    def test_closeup_target_must_preserve_exact_source_trailing_newlines(self):
        row = next(row for row in self.rows if row[0] == "CLOSEUP_BATCH" and row[1] == "observable_kingsnotes")
        self.assertTrue(VERIFY.decoded(row[4]).endswith("\n\n"))
        row[4] = encoded(VERIFY.decoded(row[4]).rstrip())
        api = next(row for row in self.rows if row[0] == "API" and row[1] == "batch:observable_kingsnotes")
        api[5], api[6] = row[4], row[4]
        self.assertFalse(self.result()["checks"]["all_closeup_complete_real_targets_displayed"])

    def test_collected_with_empty_getter_is_rejected(self):
        for row in self.component_rows("characters.body"):
            if row[0] == "TEXT" and row[2] in {"translated", "restored"}:
                row[5] = ""
            elif row[0] == "API":
                row[6], row[7] = "", "False"
            elif row[0] == "ROUNDTRIP":
                row[4], row[5] = "", ""
        result = self.result()
        self.assertTrue(result["checks"]["collection_finished"])
        self.assertFalse(result["checks"]["characters_body_actual_translation"])
        self.assertFalse(result["passed"])

    def test_f8_unchanged_chinese_is_not_original(self):
        component = self.component_rows("characters.name")
        target = next(row[5] for row in component if row[0] == "TEXT" and row[2] == "translated")
        for row in component:
            if row[0] == "TEXT" and row[2] == "original":
                row[5] = target
            elif row[0] == "API":
                row[3] = target
            elif row[0] == "ROUNDTRIP":
                row[3] = target
        self.assertFalse(self.result()["checks"]["characters_name_actual_translation"])

    def test_found_api_with_actual_english_is_rejected(self):
        component = self.component_rows("leads.body")
        source = next(row[5] for row in component if row[0] == "TEXT" and row[2] == "original")
        for row in component:
            if row[0] == "TEXT" and row[2] in {"translated", "restored"}:
                row[5] = source
            elif row[0] == "API":
                row[6], row[7] = source, "True"
            elif row[0] == "ROUNDTRIP":
                row[4], row[5] = source, source
        result = self.result()
        self.assertFalse(result["checks"]["api_reported_matches_consistent"])
        self.assertFalse(result["checks"]["leads_body_actual_translation"])

    def test_false_roundtrip_boolean_cannot_hide_restoration_difference(self):
        for row in self.component_rows("timeline.detail"):
            if row[0] == "TEXT" and row[2] == "restored":
                row[5] = encoded(self.documents["observable_hamletdiary"][1])
            elif row[0] == "ROUNDTRIP":
                row[5], row[6] = encoded(self.documents["observable_hamletdiary"][1]), "True"
        result = self.result()
        self.assertFalse(result["checks"]["f8_roundtrip_matches"])
        self.assertFalse(result["checks"]["timeline_detail_actual_translation"])

    def test_missing_real_rumor_data_is_uncovered(self):
        self.rows = [row for row in self.rows if not (row[0] == "CONTROL" and row[2].startswith("rumors."))]
        self.rows.append(["UNAVAILABLE", "rumors.body", "真实资料未开放"])
        result = self.result()
        self.assertIn("rumors.body", result["uncovered_roles"])
        self.assertFalse(result["passed"])

    def test_real_document_hash_mismatch_is_rejected(self):
        row = next(row for row in self.rows if row[0] == "DOCUMENT_SOURCE")
        row[2] = encoded(VERIFY.decoded(row[2]) + " ")
        self.assertFalse(self.result()["checks"]["real_document_sources_match"])

    def test_log_requires_real_overlay_owner(self):
        row = next(row for row in self.rows if row[0] == "NAV_OWNER" and row[1] == "log")
        row[3] = "overlay=False"
        result = self.result()
        self.assertTrue(result["checks"]["all_real_navigation_confirmed"])
        self.assertFalse(result["checks"]["real_log_overlay_owned"])
        self.assertFalse(result["passed"])

    def test_component_cache_found_does_not_prove_display(self):
        row = next(row for row in self.rows if row[0] == "API" and row[2] == "component_string_bool")
        row[6], row[7] = row[3], "True"
        self.assertFalse(self.result()["checks"]["real_document_body_components_translated"])

    def test_clock_refresh_cannot_pass_with_equal_text_snapshots(self):
        row = next(row for row in self.rows if row[0] == "CLOCK" and row[1:3] == ["hud", "after"])
        row[4] = encoded("1234.6")
        result = self.result()
        self.assertTrue(result["checks"]["hud_time_actual_translation"])
        self.assertFalse(result["checks"]["all_phase_clocks_really_paused_and_stable"])
        self.assertFalse(result["passed"])

    def test_clock_value_unchanged_without_pause_is_rejected(self):
        for row in self.rows:
            if row[0] == "CLOCK" and row[1] == "hud":
                row[3] = "0"
        self.assertFalse(self.result()["checks"]["all_phase_clocks_really_paused_and_stable"])

    def test_unavailable_phase_cannot_be_hidden_by_collected(self):
        self.rows.append(["UNAVAILABLE", "timeline", "真实阶段未完成"])
        result = self.result()
        self.assertTrue(result["checks"]["collection_finished"])
        self.assertFalse(result["checks"]["all_requested_phases_available"])
        self.assertFalse(result["passed"])

    def test_second_log_untranslated_cannot_hide_behind_first(self):
        source = next(row[2] for row in self.rows if row[0] == "HISTORY_SOURCE" and row[1] == "1")
        self.replace_log_display(1, VERIFY.decoded(source), found=False)
        result = self.result()
        self.assertTrue(result["checks"]["log_entry_actual_translation"])
        self.assertTrue(result["log_entries"][0]["translated"])
        self.assertFalse(result["log_entries"][1]["translated"])
        self.assertFalse(result["passed"])

    def test_second_log_partial_translation_cache_hit_is_rejected(self):
        self.replace_log_display(1, "哈姆雷特的私人日记。Ophelia wakes up.")
        result = self.result()
        self.assertTrue(result["log_entries"][1]["whole_source_cache_matches"])
        self.assertIn("Ophelia", result["log_entries"][1]["unapproved_english"])
        self.assertFalse(result["checks"]["log_all_entries_completely_translated"])
        self.assertFalse(result["passed"])

    def test_second_log_missing_index_binding_is_rejected(self):
        self.rows = [row for row in self.rows if not (row[0] == "LOG_ENTRY" and row[1] == "1")]
        self.assertFalse(self.result()["checks"]["log_all_real_history_indices_bound"])

    def test_log_indices_cannot_reuse_first_component(self):
        first = next(row for row in self.rows if row[0] == "LOG_ENTRY" and row[1] == "0")
        second = next(row for row in self.rows if row[0] == "LOG_ENTRY" and row[1] == "1")
        second[2] = first[2]
        self.assertFalse(self.result()["checks"]["log_all_real_history_indices_bound"])

    def test_second_log_original_must_equal_real_history_source(self):
        binding = next(row for row in self.rows if row[0] == "LOG_ENTRY" and row[1] == "1")
        component = binding[2]
        wrong_source = encoded(self.documents["observable_poldesk"][0])
        for row in self.rows:
            if row[0] == "TEXT" and row[1:4] == ["log", "original", component]:
                row[5] = wrong_source
            elif row[0] == "API" and row[1:3] == ["log", component]:
                row[3] = wrong_source
            elif row[0] == "ROUNDTRIP" and row[1:3] == ["log", component]:
                row[3] = wrong_source
            elif row[0] == "LOG_ROUNDTRIP" and row[1] == "1":
                row[4], row[7] = wrong_source, "True"
        result = self.result()
        self.assertTrue(result["checks"]["f8_roundtrip_matches"])
        self.assertFalse(result["checks"]["log_all_entries_f8_original_exact"])

    def test_known_markup_and_keys_do_not_count_as_english_body(self):
        self.replace_log_display(1, '<b>哈姆雷特的私人日记</b><sprite name="KeyboardF8">按F8、[W]或Ctrl+C。')
        self.assertTrue(self.result()["checks"]["log_all_entries_completely_translated"])

    def test_unknown_markup_cannot_mask_english_body(self):
        self.replace_log_display(1, "哈姆雷特的私人日记<UntranslatedDialogue>Ophelia wakes up</UntranslatedDialogue>")
        self.assertFalse(self.result()["checks"]["log_no_unapproved_english"])

    def test_long_backerbook_cannot_pass_with_partial_display(self):
        row = next(row for row in self.rows if row[0] == "CLOSEUP_BATCH" and row[1] == "observable_backerbook4")
        row[4] = encoded("<line-height=90%>只有开头译成中文。May Day's Eve")
        api = next(row for row in self.rows if row[0] == "API" and row[1] == "batch:observable_backerbook4")
        api[5], api[6], api[7] = row[4], row[4], "True"
        self.assertFalse(self.result()["checks"]["all_closeup_complete_real_targets_displayed"])

    def test_closeup_batch_requires_all_real_ids(self):
        self.rows = [row for row in self.rows if not (row[0] == "CLOSEUP_BATCH" and row[1] == "observable_backerbook3")]
        self.assertFalse(self.result()["checks"]["all_closeup_frozen_ids_consumed"])

    def test_brit_multiline_title_or_overlap_is_rejected(self):
        title = next(row for row in self.rows if row[0] == "CHARACTER_GEOMETRY" and row[1:3] == ["brit", "title"])
        title[4], title[9] = "2", "30"
        self.assertFalse(self.result()["checks"]["all_known_character_titles_fit_without_overlap"])

    def test_falsely_reported_no_overlap_cannot_hide_bounds_intersection(self):
        title = next(row for row in self.rows if row[0] == "CHARACTER_GEOMETRY" and row[1:3] == ["brit", "title"])
        title[9] = "30"
        self.assertFalse(self.result()["checks"]["all_known_character_titles_fit_without_overlap"])

    def test_quoted_preview_cannot_pass_with_english_inside_quotes(self):
        source = next(row[1] for row in self.rows if row[0] == "PRESENT_PREVIEW_SOURCE")
        row = next(row for row in self.rows if row[0] == "API" and row[1:3] == ["present", "builder:PresentPreviewText"])
        row[5], row[6], row[7] = source, source, "True"
        self.assertFalse(self.result()["checks"]["real_quoted_information_preview_translated"])

    def set_preview_case(self, source, target, information_id, scene_id):
        firstline = source[1:-1]
        for row in self.rows:
            if row[0] == "PRESENT_PREVIEW_SOURCE":
                row[1] = encoded(source)
            elif row[0] == "PRESENT_PREVIEW_ORIGIN":
                row[1:] = [encoded(information_id), encoded("gertrude"), encoded(scene_id), encoded(firstline),
                           hashlib.sha256(firstline.encode()).hexdigest(), hashlib.sha256(source.encode()).hexdigest()]
            elif row[0] == "TEXT" and row[1] == "present":
                row[5] = encoded(source if row[2] == "original" else target)
            elif row[0] == "API" and row[1] == "present":
                row[3], row[5], row[6] = encoded(source), encoded(target), encoded(target)
            elif row[0] == "ROUNDTRIP" and row[1] == "present":
                row[3], row[4], row[5] = encoded(source), encoded(target), encoded(target)

    def test_current_real_information_can_pass_without_danger_scene(self):
        tests = json.loads((ROOT / "translation/supplemental/notification-ui-tests.json").read_text(encoding="utf-8-sig"))
        source = '"Hamlet is acting incredibly strangely lately. Do you know what\'s wrong?"'
        target = next(row["target"] for row in tests if row["source"] == source)
        self.set_preview_case(source, target, "HamletActingMad", "Gertrude_FoulMood")
        result = self.result()
        self.assertTrue(result["passed"])
        self.assertFalse(result["information_preview"]["danger_scene_in_this_ui_run"])
        self.assertTrue(result["checks"]["danger_preview_existing_real_consumer_coverage"])

    def test_unknown_preview_cannot_pass_with_api_and_chinese(self):
        self.set_preview_case('"Unknown invented information."', "“未知信息。”", "HamletActingMad", "Gertrude_FoulMood")
        result = self.result()
        self.assertTrue(result["checks"]["f8_roundtrip_matches"])
        self.assertFalse(result["checks"]["real_information_preview_source_whitelisted"])
        self.assertFalse(result["checks"]["real_quoted_information_preview_translated"])

    def test_preview_scene_and_information_must_match_real_origin(self):
        origin = next(row for row in self.rows if row[0] == "PRESENT_PREVIEW_ORIGIN")
        origin[3] = encoded("Gertrude_FoulMood")
        self.assertFalse(self.result()["checks"]["real_information_preview_source_whitelisted"])

    def test_preview_origin_hash_cannot_be_forged(self):
        origin = next(row for row in self.rows if row[0] == "PRESENT_PREVIEW_ORIGIN")
        origin[5] = "0" * 64
        self.assertFalse(self.result()["checks"]["real_information_preview_source_whitelisted"])

    def test_preview_partial_chinese_cannot_replace_complete_frozen_target(self):
        source = next(VERIFY.decoded(row[1]) for row in self.rows if row[0] == "PRESENT_PREVIEW_SOURCE")
        self.set_preview_case(source, "“只有部分。”", "SomeoneKillingMe", "hamlet_SomeoneKillingMe")
        result = self.result()
        self.assertTrue(result["checks"]["real_information_preview_source_whitelisted"])
        self.assertFalse(result["checks"]["real_quoted_information_preview_translated"])


if __name__ == "__main__":
    unittest.main()
