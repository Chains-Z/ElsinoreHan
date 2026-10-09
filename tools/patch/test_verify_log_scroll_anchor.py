"""阅读锚点判定器异常回归；夹具不是真实游戏布局验收。"""

import base64
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("scroll_verifier", Path(__file__).with_name("verify-log-scroll-anchor.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def enc(value):
    return base64.b64encode(value.encode()).decode()


def fixture():
    sources = ["Short real history.\nSecond.", "Long actual historical dialogue.\nMuch longer second part.\nThird paragraph."]
    targets = ["真实短历史。\n第二段。", "实际历史对白的长段落。\n较长的第二部分。\n第三段。"]
    rows = [["SCHEMA", "1"], ["SAVE_GUARD_ACTIVE", "True"], ["PHYSICAL_INPUT_GUARD_ACTIVE", "True"],
            ["NAVIGATION", "log", "True", "True"], ["HISTORY_COUNT", "2"]]
    journal = []
    for index in range(2):
        rows.append(["HISTORY", str(index), str(index + 100), enc(sources[index])])
        journal += [["HISTORY_SOURCE", str(index), enc(sources[index])],
                    ["LOG_ENTRY", str(index), str(index + 100)],
                    ["TEXT", "log", "translated", str(index + 100), enc("UI/Log"), enc(targets[index])]]
    token = 1
    for name, intended, kind, actual, paragraph in (("middle", -1, "middle", 1, 1), ("short", 0, "short", 0, 0),
                                                    ("long-upper", 1, "long", 1, 0), ("long-lower", 1, "long", 1, 2)):
        rows.append(["CASE", name, str(intended), kind])
        for mode in ("original", "restored"):
            for stage in ("before", "after"):
                translated = (mode == "original") == (stage == "before")
                rows.append(["SAMPLE", name, mode, stage, str(actual), str(actual + 100), str(paragraph), "-20",
                             "True", "-20", "captured" if stage == "before" else "restored", "0",
                             str(translated), "True", enc(sources[actual]), enc(targets[actual] if translated else sources[actual]), str(token)])
                token += 1
    rows.append(["STATUS", "COLLECTED"])
    return rows, journal


def analyze(rows, journal):
    return MODULE.analyze("\n".join("\t".join(row) for row in rows), "\n".join("\t".join(row) for row in journal))


class ScrollAnchorTests(unittest.TestCase):
    def test_complete_real_component_contract_passes(self):
        self.assertTrue(analyze(*fixture())["passed"])

    def test_guard_false_or_absent_fails(self):
        for tag in ("SAVE_GUARD_ACTIVE", "PHYSICAL_INPUT_GUARD_ACTIVE"):
            rows, journal = fixture()
            next(row for row in rows if row[0] == tag)[1] = "False"
            self.assertFalse(analyze(rows, journal)["passed"])

    def test_proportional_position_but_different_paragraph_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:4] == ["SAMPLE", "middle", "original", "after"])[6] = "2"
        self.assertFalse(analyze(rows, journal)["checks"]["same_entry_and_paragraph"])

    def test_helper_claim_without_matching_actual_geometry_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:4] == ["SAMPLE", "middle", "original", "after"])[9] = "400"
        self.assertFalse(analyze(rows, journal)["checks"]["baseline_restored_within_one_ui_unit"])

    def test_inactive_mesh_or_missing_mesh_fails(self):
        for column in (8, 13):
            rows, journal = fixture()
            next(row for row in rows if row[:4] == ["SAMPLE", "middle", "original", "after"])[column] = "False"
            self.assertFalse(analyze(rows, journal)["checks"]["active_real_mesh_coordinates"])

    def test_nan_or_infinite_coordinate_fails(self):
        for value in ("nan", "inf", "-inf"):
            rows, journal = fixture()
            next(row for row in rows if row[:4] == ["SAMPLE", "middle", "original", "after"])[9] = value
            self.assertFalse(analyze(rows, journal)["passed"])

    def test_stale_completed_anchor_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:4] == ["SAMPLE", "middle", "original", "after"])[16] = "1"
        self.assertFalse(analyze(rows, journal)["checks"]["fresh_official_toggle_completion"])

    def test_clamped_or_skipped_outcome_is_not_precise_restore(self):
        for value in ("boundary-clamped", "paragraphs-changed", "closed", "history-changed"):
            rows, journal = fixture()
            next(row for row in rows if row[:4] == ["SAMPLE", "middle", "original", "after"])[10] = value
            self.assertFalse(analyze(rows, journal)["passed"])

    def test_unknown_or_changed_history_source_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[0] == "HISTORY")[3] = enc("Invented.")
        self.assertFalse(analyze(rows, journal)["checks"]["history_bound_to_journal"])

    def test_real_log_title_and_other_text_controls_are_not_history(self):
        rows, journal = fixture()
        journal += [["TEXT", "log", "translated", "36588", enc("UI/Log/Title"), enc("对话记录")],
                    ["TEXT", "log", "translated", "999", enc("UI/Log/Close/Tooltip"), enc("关闭")]]
        self.assertTrue(analyze(rows, journal)["passed"])

    def test_title_cannot_replace_missing_declared_history_text(self):
        rows, journal = fixture()
        journal = [row for row in journal if not (row[:3] == ["TEXT", "log", "translated"] and row[3] == "100")]
        journal.append(["TEXT", "log", "translated", "36588", enc("UI/Log/Title"), enc("对话记录")])
        self.assertFalse(analyze(rows, journal)["checks"]["history_bound_to_journal"])

    def test_duplicate_declared_history_text_fails_despite_other_controls(self):
        rows, journal = fixture()
        journal.append(copy.copy(next(row for row in journal if row[:3] == ["TEXT", "log", "translated"])))
        journal.append(["TEXT", "log", "translated", "36588", enc("UI/Log/Title"), enc("对话记录")])
        self.assertFalse(analyze(rows, journal)["checks"]["history_bound_to_journal"])

    def test_original_and_restored_text_must_match_bound_history(self):
        for leg in ("original", "restored"):
            rows, journal = fixture()
            next(row for row in rows if row[:4] == ["SAMPLE", "middle", leg, "after"])[15] = enc("")
            self.assertFalse(analyze(rows, journal)["checks"]["f8_text_exact"])

    def test_duplicate_sample_or_missing_case_fails(self):
        rows, journal = fixture()
        rows.append(copy.copy(next(row for row in rows if row[0] == "SAMPLE")))
        self.assertFalse(analyze(rows, journal)["passed"])
        rows, journal = fixture()
        rows = [row for row in rows if not (row[0] == "CASE" and row[1] == "short")]
        self.assertFalse(analyze(rows, journal)["passed"])

    def test_long_cases_cannot_repeat_same_reading_position(self):
        rows, journal = fixture()
        for row in rows:
            if row[:2] == ["SAMPLE", "long-lower"]:
                row[6] = "0"
        self.assertFalse(analyze(rows, journal)["checks"]["short_long_real_history"])

    def test_incomplete_capture_or_unknown_schema_cannot_pass(self):
        rows, journal = fixture()
        rows.append(["UNAVAILABLE", "middle", enc("没有真实mesh")])
        self.assertFalse(analyze(rows, journal)["passed"])
        rows, journal = fixture()
        rows.append(["SYNTHETIC_HISTORY", "bad"])
        self.assertFalse(analyze(rows, journal)["checks"]["schema_valid"])


if __name__ == "__main__":
    unittest.main()
