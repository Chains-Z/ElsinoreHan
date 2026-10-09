"""地图确认框判定器的缺失、失活、漏译及取消状态异常回归；夹具不是游戏采集。"""

import base64
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("map_followup", Path(__file__).with_name("verify-map-followup.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE = "Go to Upper Hallway?"
TARGET = "前往上层走廊？"
EXPECTED = {SOURCE: {"target": TARGET, "parameter_kind": "room", "parameter_source": "Upper Hallway"}}


def enc(value):
    return base64.b64encode(value.encode("utf-8")).decode()


def fixture():
    rows = [["SCHEMA", "1"], ["SAVE_GUARD_ACTIVE", "True"], ["PHYSICAL_INPUT_GUARD_ACTIVE", "True"],
            ["NAVIGATION", "map", "True", "True"], ["POSITION", "before", enc("UpperHallway"), "1", "2", "3"],
            ["CLOCK", "before", "2", "480"], ["CASE", "upper-hallway", "room", enc("Upper Hallway"), enc("UI/Map/UpperHallway")],
            ["CLICK", "upper-hallway", enc("UI/Map/UpperHallway"), "True"],
            ["SOURCE", "upper-hallway", enc(SOURCE)], ["API", "upper-hallway", "True", enc(TARGET)]]
    for mode in ("translated", "original", "restored"):
        rows.append(["SAMPLE", "upper-hallway", mode, "100", enc("UI/Map/ConfirmMoveDialog/DialogText(Clone)"),
                     enc(SOURCE), enc(SOURCE if mode == "original" else TARGET), "True", "False" if mode == "original" else "True"])
    rows += [["CLICK", "upper-hallway.no", enc("UI/Map/ConfirmMoveDialog/No"), "True"],
             ["CANCEL", "upper-hallway", "1", "True", "True"],
             ["UNAVAILABLE", "hamlet", enc("当前真实楼层没有可交互Hamlet图标")],
             ["POSITION", "after", enc("UpperHallway"), "1", "2", "3"], ["CLOCK", "after", "2", "480"],
             ["STATUS", "COLLECTED"]]
    return rows


def analyze(rows):
    return MODULE.analyze("\n".join("\t".join(row) for row in rows), EXPECTED)


class MapFollowupTests(unittest.TestCase):
    def test_complete_real_source_contract_passes_and_hamlet_is_uncovered(self):
        result = analyze(fixture())
        self.assertTrue(result["passed"])
        self.assertFalse(result["hamlet_covered"])

    def test_missing_or_false_guards_fail(self):
        for tag in ("SAVE_GUARD_ACTIVE", "PHYSICAL_INPUT_GUARD_ACTIVE"):
            rows = fixture()
            next(row for row in rows if row[0] == tag)[1] = "False"
            self.assertFalse(analyze(rows)["passed"])

    def test_missing_screenshot_case_cannot_be_replaced_by_other_room(self):
        rows = fixture()
        for row in rows:
            if len(row) > 1 and row[1] == "upper-hallway":
                row[1] = "other-room"
        self.assertFalse(analyze(rows)["checks"]["upper_hallway_covered"])

    def test_found_but_english_cache_is_rejected(self):
        rows = fixture()
        next(row for row in rows if row[0] == "API")[3] = enc(SOURCE)
        self.assertFalse(analyze(rows)["checks"]["cache_matches_frozen"])

    def test_empty_or_untranslated_display_cannot_pass_roundtrip(self):
        for value in ("", SOURCE):
            rows = fixture()
            for row in rows:
                if row[0] == "SAMPLE" and row[2] != "original":
                    row[6] = enc(value)
            self.assertFalse(analyze(rows)["checks"]["translated_restored_exact"])

    def test_original_requires_exact_real_english(self):
        rows = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "upper-hallway", "original"])[6] = enc(TARGET)
        self.assertFalse(analyze(rows)["checks"]["english_original_exact"])

    def test_original_or_restored_inactive_is_rejected(self):
        for mode in ("original", "restored"):
            rows = fixture()
            next(row for row in rows if row[:3] == ["SAMPLE", "upper-hallway", mode])[7] = "False"
            self.assertFalse(analyze(rows)["checks"]["all_three_active_modes"])

    def test_missing_duplicate_or_different_component_samples_fail(self):
        rows = fixture()
        rows = [row for row in rows if row[:3] != ["SAMPLE", "upper-hallway", "restored"]]
        self.assertFalse(analyze(rows)["passed"])
        rows = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "upper-hallway", "restored"])[3] = "101"
        self.assertFalse(analyze(rows)["checks"]["same_component_and_source"])

    def test_signed_nonzero_unity_component_id_is_valid(self):
        rows = fixture()
        for row in rows:
            if row[0] == "SAMPLE":
                row[3] = "-100"
        self.assertTrue(analyze(rows)["passed"])

    def test_builder_changed_by_translation_is_rejected(self):
        rows = fixture()
        next(row for row in rows if row[0] == "SAMPLE")[5] = enc(TARGET)
        self.assertFalse(analyze(rows)["checks"]["same_component_and_source"])

    def test_yes_or_early_cancel_is_rejected(self):
        rows = fixture()
        next(row for row in rows if row[0] == "CANCEL")[2] = "0"
        self.assertFalse(analyze(rows)["checks"]["cancelled_only_with_no"])
        rows = fixture()
        cancellation = next(row for row in rows if row[0] == "CANCEL")
        rows.remove(cancellation)
        rows.insert(1, cancellation)
        self.assertFalse(analyze(rows)["checks"]["cancelled_only_with_no"])

    def test_player_position_or_room_change_is_rejected(self):
        for index, value in ((2, enc("LowerHallway")), (3, "2"), (3, "nan")):
            rows = fixture()
            next(row for row in rows if row[:2] == ["POSITION", "after"])[index] = value
            self.assertFalse(analyze(rows)["checks"]["player_location_unchanged"])

    def test_running_or_changed_clock_is_rejected(self):
        for index, value in ((2, "0"), (3, "481"), (3, "nan")):
            rows = fixture()
            next(row for row in rows if row[:2] == ["CLOCK", "after"])[index] = value
            self.assertFalse(analyze(rows)["checks"]["paused_clock_unchanged"])

    def test_hamlet_unavailable_record_cannot_be_omitted(self):
        rows = [row for row in fixture() if row[0] != "UNAVAILABLE"]
        self.assertFalse(analyze(rows)["checks"]["hamlet_coverage_recorded"])

    def test_failures_or_malformed_samples_cannot_pass(self):
        rows = fixture() + [["FAILURE", enc("真实页面已关闭")]]
        self.assertFalse(analyze(rows)["passed"])
        rows = fixture()
        next(row for row in rows if row[0] == "SAMPLE").pop()
        self.assertFalse(analyze(rows)["passed"])


if __name__ == "__main__":
    unittest.main()
