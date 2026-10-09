"""构造故障报告核查验收判定；使用冻结真实文档片段，不作为游戏E2E。"""

import base64
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
    def setUp(self):
        resources = json.loads(RESOURCE_PATH.read_text(encoding="utf-8-sig"))
        self.documents = {
            row["origin"]["record_id"]: (row["source"], row["target"])
            for row in resources
            if row.get("origin", {}).get("asset") == "closeups"
            and row["origin"].get("field") == "text"
            and row["origin"].get("record_id") in {"observable_hamletdiary", "observable_poldesk"}
        }
        self.directory = tempfile.TemporaryDirectory(dir=ROOT / "runtime/build")
        self.addCleanup(self.directory.cleanup)
        self.report = Path(self.directory.name) / "journal-ui.txt"
        self.rows = [["STATUS", "COLLECTED"], ["SAVE_WRITE_GUARD_ACTIVE", "True"]]
        phases = ["hud", "journal", "timeline", "log"] + list(self.documents)
        self.rows += [["NAVIGATION", phase, "真实页面字段", "True"] for phase in phases]
        self.rows.append(["NAV_OWNER", "log", "modal=False", "overlay=True"])
        self.rows += [["TAB", tab, str(index)] for index, tab in enumerate(["CharactersTab", "HearsayTab", "LeadsTab"])]
        self.rows += [["DOCUMENT_SOURCE", key, encoded(source)] for key, (source, _) in self.documents.items()]
        roles = {
            "hud": ["hud.time", "hud.room"], "CharactersTab": ["characters.name", "characters.body"],
            "LeadsTab": ["leads.title", "leads.body"], "HearsayTab": ["rumors.title", "rumors.body"],
            "timeline": ["timeline.detail"], "log": ["log.entry"],
            "observable_hamletdiary": ["document.body"], "observable_poldesk": ["document.body"],
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

    def result(self):
        self.report.write_text("\n".join("\t".join(row) for row in self.rows) + "\n", encoding="utf-8")
        return VERIFY.analyze(self.report, RESOURCE_PATH)

    def control(self, role):
        return next(row for row in self.rows if row[0] == "CONTROL" and row[2] == role)

    def component_rows(self, role):
        control = self.control(role)
        return [row for row in self.rows if row[0] in {"TEXT", "API", "ROUNDTRIP"}
                and row[1] == control[1] and row[3 if row[0] == "TEXT" else 2] == control[3]]

    def test_complete_consistent_report_passes(self):
        self.assertTrue(self.result()["passed"])

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


if __name__ == "__main__":
    unittest.main()
