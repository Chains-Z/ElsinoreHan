"""斜体几何判定异常分支回归；数据是判定器单元夹具，不冒称真实网格。"""

import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("italic_geometry", Path(__file__).with_name("verify-italic-geometry.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    result = {"schema": 1, "fontRestored": True, "originalItalicStyle": 35,
              "repairedItalicStyle": 10, "samples": []}
    for layout in ("dialogue", "log"):
        for source in sorted(MODULE.SOURCE_IDS):
            for mode in ("old", "repaired", "normal"):
                characters = []
                plain, emphasized = MODULE.expected_characters(source)
                for i, text in enumerate(plain):
                    italic = mode != "normal" and i in emphasized
                    padding = -2.0 if mode == "old" and italic else 0.5 if italic else 1.0
                    characters.append({"index": i, "line": 0, "text": text, "origin": i * 10.0,
                                       "advance": (i + 1) * 10.0, "inkLeft": i * 10 + padding,
                                       "inkRight": (i + 1) * 10 - padding, "font": "ARIALUNI SDF",
                                       "italic": italic,
                                       "tilt": (3.5 if mode == "old" else 1.0) if italic else 0.0})
                result["samples"].append({"layout": layout, "sourceId": source, "mode": mode,
                                          "text": plain if mode == "normal" else MODULE.SOURCE_TEXTS[source],
                                          "italicStyle": 35 if mode == "old" else 10,
                                          "width": 500.0, "fontSize": 24.0,
                                          "characters": characters,
                                          "boundaries": []})
                refresh_boundaries(result["samples"][-1])
    return result


def refresh_boundaries(sample):
    """夹具同时变动网格与派生gap，避免独立填入判定结果。"""
    sample["boundaries"] = [{"left": a["index"], "right": b["index"],
                             "gap": b["inkLeft"] - a["inkRight"]}
                            for a, b in zip(sample["characters"], sample["characters"][1:])
                            if a["line"] == b["line"] and a["italic"] != b["italic"]]


class GeometryTests(unittest.TestCase):
    def test_expected_texts_match_frozen_real_translations(self):
        root = Path(__file__).resolve().parents[2]
        rows = json.loads((root / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        actual = {row["id"]: row["target"] for row in rows if row["id"] in MODULE.SOURCE_IDS}
        self.assertEqual(actual, MODULE.SOURCE_TEXTS)

    def test_complete_comparison_passes(self):
        self.assertTrue(MODULE.analyze(fixture())["passed"])

    def test_missing_layout_fails(self):
        report = fixture()
        report["samples"] = [s for s in report["samples"] if s["layout"] != "log"]
        self.assertFalse(MODULE.analyze(report)["checks"]["all_twelve_samples"])

    def test_remaining_collision_fails(self):
        report = fixture()
        report["samples"][1]["boundaries"][0]["gap"] = -0.5
        self.assertFalse(MODULE.analyze(report)["checks"]["repaired_ink_boundaries_clear"])

    def test_removed_emphasis_fails(self):
        report = fixture()
        next(c for c in report["samples"][1]["characters"] if c["italic"])["tilt"] = 0.0
        self.assertFalse(MODULE.analyze(report)["checks"]["italic_retained"])

    def test_normal_control_detects_bad_mapping(self):
        report = fixture()
        report["samples"][2]["characters"][0]["tilt"] = 0.8
        self.assertFalse(MODULE.analyze(report)["checks"]["normal_not_slanted"])

    def test_changed_advance_fails(self):
        report = fixture()
        report["samples"][1]["characters"][1]["advance"] += 2
        self.assertFalse(MODULE.analyze(report)["checks"]["character_advance_unchanged"])

    def test_not_restored_fails(self):
        report = fixture()
        report["fontRestored"] = False
        self.assertFalse(MODULE.analyze(report)["passed"])

    def test_nonfinite_bounds_fail(self):
        report = fixture()
        report["samples"][1]["characters"][1]["inkLeft"] = float("nan")
        self.assertFalse(MODULE.analyze(report)["checks"]["all_geometry_finite"])

    def test_no_old_collision_cannot_claim_reproduction(self):
        report = fixture()
        for sample in report["samples"]:
            for character in sample["characters"]:
                character["inkLeft"] = character["origin"] + 1
                character["inkRight"] = character["advance"] - 1
            refresh_boundaries(sample)
        self.assertFalse(MODULE.analyze(report)["checks"]["old_collision_reproduced"])

    def test_empty_characters_cannot_pass_on_fabricated_boundaries(self):
        report = fixture()
        for sample in report["samples"]:
            sample["characters"] = []
        self.assertFalse(MODULE.analyze(report)["checks"]["nonempty_character_samples"])
        self.assertFalse(MODULE.analyze(report)["passed"])

    def test_missing_nested_arrays_fail_without_exception(self):
        report = fixture()
        del report["samples"][0]["characters"]
        self.assertFalse(MODULE.analyze(report)["passed"])
        report = fixture()
        del report["samples"][0]["boundaries"]
        self.assertFalse(MODULE.analyze(report)["passed"])

    def test_each_mode_style_must_match_metadata(self):
        for index in (0, 1, 2):
            with self.subTest(mode=index):
                report = fixture()
                report["samples"][index]["italicStyle"] = 20
                self.assertFalse(MODULE.analyze(report)["checks"]["mode_style_consistent"])

    def test_original_style_must_be_actual_thirty_five(self):
        report = fixture()
        report["originalItalicStyle"] = 30
        self.assertFalse(MODULE.analyze(report)["checks"]["actual_old_style_recorded"])

    def test_invalid_layout_dimensions_fail(self):
        for field in ("width", "fontSize"):
            for value in (None, 0, -1, float("nan"), float("inf"), "24", True):
                with self.subTest(field=field, value=value):
                    report = fixture()
                    report["samples"][1][field] = value
                    self.assertFalse(MODULE.analyze(report)["checks"]["layout_geometry_consistent"])

    def test_three_mode_layout_dimensions_must_agree(self):
        for field in ("width", "fontSize"):
            with self.subTest(field=field):
                report = fixture()
                report["samples"][1][field] += 1
                self.assertFalse(MODULE.analyze(report)["checks"]["layout_geometry_consistent"])

    def test_boundary_must_reference_actual_adjacent_characters(self):
        for field, value in (("left", -1), ("right", 999), ("left", 0), ("right", True)):
            with self.subTest(field=field, value=value):
                report = fixture()
                report["samples"][1]["boundaries"][0][field] = value
                self.assertFalse(MODULE.analyze(report)["checks"]["boundary_evidence_valid"])

    def test_boundary_must_be_same_line(self):
        report = fixture()
        sample = report["samples"][1]
        right = sample["boundaries"][0]["right"]
        sample["characters"][right]["line"] = 1
        self.assertFalse(MODULE.analyze(report)["checks"]["boundary_evidence_valid"])

    def test_duplicate_boundary_cannot_replace_missing_boundary(self):
        report = fixture()
        sample = report["samples"][1]
        sample["boundaries"][1] = dict(sample["boundaries"][0])
        self.assertFalse(MODULE.analyze(report)["checks"]["boundary_evidence_valid"])

    def test_malformed_boundary_reference_fails_without_exception(self):
        report = fixture()
        report["samples"][0]["boundaries"][0]["left"] = []
        self.assertFalse(MODULE.analyze(report)["passed"])

    def test_reported_gap_must_equal_actual_ink_bounds(self):
        report = fixture()
        report["samples"][1]["boundaries"][0]["gap"] += 10
        self.assertFalse(MODULE.analyze(report)["checks"]["boundary_evidence_valid"])

    def test_normal_mode_cannot_invent_emphasis_boundary(self):
        report = fixture()
        report["samples"][2]["boundaries"] = [{"left": 0, "right": 1, "gap": 2}]
        self.assertFalse(MODULE.analyze(report)["checks"]["boundary_evidence_valid"])

    def test_expected_source_text_cannot_be_replaced(self):
        report = fixture()
        report["samples"][1]["text"] = "伪造正文"
        self.assertFalse(MODULE.analyze(report)["checks"]["expected_text_and_emphasis"])

    def test_all_modes_missing_same_character_cannot_pass(self):
        report = fixture()
        for sample in report["samples"][:3]:
            sample["characters"].pop()
        self.assertFalse(MODULE.analyze(report)["checks"]["expected_text_and_emphasis"])

    def test_all_modes_reordered_same_characters_cannot_pass(self):
        report = fixture()
        for sample in report["samples"][:3]:
            sample["characters"][0]["text"], sample["characters"][1]["text"] = (
                sample["characters"][1]["text"], sample["characters"][0]["text"])
        self.assertFalse(MODULE.analyze(report)["checks"]["expected_text_and_emphasis"])

    def test_changed_character_index_fails(self):
        report = fixture()
        report["samples"][1]["characters"][0]["index"] = 999
        self.assertFalse(MODULE.analyze(report)["checks"]["expected_text_and_emphasis"])

    def test_emphasis_outside_frozen_span_fails(self):
        report = fixture()
        report["samples"][1]["characters"][0]["italic"] = True
        self.assertFalse(MODULE.analyze(report)["checks"]["expected_text_and_emphasis"])

    def test_old_emphasis_also_must_match_frozen_span(self):
        report = fixture()
        next(c for c in report["samples"][0]["characters"] if c["italic"])["italic"] = False
        self.assertFalse(MODULE.analyze(report)["checks"]["expected_text_and_emphasis"])


if __name__ == "__main__":
    unittest.main()
