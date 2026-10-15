"""底部锚点判定器的局部异常回归，模拟报告不代表游戏布局验收。"""

import base64
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("bottom_verifier", Path(__file__).with_name("verify-log-bottom-anchor.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    encode = lambda text: base64.b64encode(text.encode()).decode()
    sources, targets = ["Earlier history.", "Final history."], ["较早历史。", "末尾历史。"]
    rows = [["SCHEMA", "1"]]
    journal = []
    for index in range(2):
        journal += [["HISTORY_SOURCE", str(index), encode(sources[index])], ["LOG_ENTRY", str(index), str(index + 100)],
                    ["TEXT", "log", "translated", str(index + 100), "", encode(targets[index])]]
    generation = 1
    for name in ("bottom-to-original", "bottom-to-translated", "manual-away"):
        for stage in ("before", "after"):
            mode = (name != "bottom-to-translated") == (stage == "before")
            away = name == "manual-away"
            index = 0 if away else 1
            rows.append(["SAMPLE", name, stage, str(mode), "0.35" if away else "0", "3500" if away else "0",
                         str(index), str(index + 100), str(generation), str(not away),
                         "captured" if stage == "before" else ("restored" if away else "bottom-restored"),
                         "1", "0", encode(sources[index]), encode(targets[index] if mode else sources[index])])
            generation += 1
    rows.append(["STATUS", "COLLECTED"])
    return rows, journal


def check(rows, journal):
    return MODULE.analyze("\n".join("\t".join(row) for row in rows), "\n".join("\t".join(row) for row in journal))


class BottomVerifierTests(unittest.TestCase):
    def test_complete_contract(self):
        self.assertTrue(check(*fixture())["passed"])

    def test_old_paragraph_success_cannot_claim_bottom_success(self):
        rows, journal = fixture()
        row = next(row for row in rows if row[:3] == ["SAMPLE", "bottom-to-original", "after"])
        row[4], row[5], row[10] = "0.0039", "128.3", "restored"
        self.assertFalse(check(rows, journal)["checks"]["both_languages_stay_at_bottom"])

    def test_bottom_claim_with_actual_distance_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "bottom-to-translated", "after"])[5] = "20"
        self.assertFalse(check(rows, journal)["passed"])

    def test_manual_scroll_cannot_be_pulled_to_bottom(self):
        rows, journal = fixture()
        row = next(row for row in rows if row[:3] == ["SAMPLE", "manual-away", "after"])
        row[4], row[9], row[10] = "0", "True", "bottom-restored"
        self.assertFalse(check(rows, journal)["checks"]["manual_scroll_uses_paragraph_anchor"])

    def test_stale_completion_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "bottom-to-original", "after"])[8] = "1"
        self.assertFalse(check(rows, journal)["checks"]["fresh_toggle_completion"])

    def test_wrong_component_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "bottom-to-original", "after"])[7] = "999"
        self.assertFalse(check(rows, journal)["checks"]["real_history_and_text"])

    def test_nan_distance_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "bottom-to-original", "after"])[5] = "nan"
        self.assertFalse(check(rows, journal)["passed"])

    def test_missing_leg_fails(self):
        rows, journal = fixture()
        rows.pop(2)
        self.assertFalse(check(rows, journal)["passed"])

    def test_partial_text_fails(self):
        rows, journal = fixture()
        next(row for row in rows if row[:3] == ["SAMPLE", "bottom-to-original", "after"])[14] = base64.b64encode(b"Incomplete.").decode()
        self.assertFalse(check(rows, journal)["checks"]["real_history_and_text"])


if __name__ == "__main__":
    unittest.main()
