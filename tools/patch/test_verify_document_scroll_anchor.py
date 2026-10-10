"""以合成记录单测判定器的拒绝行为；这些用例不是游戏布局验收。"""

import base64
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("document_verifier", Path(__file__).with_name("verify-document-scroll-anchor.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def enc(value):
    return base64.b64encode(value.encode()).decode()


def fixture():
    identifier, source, target = "observable_unit_fixture", enc("a\nb\nc"), enc("甲\n乙\n丙")
    rows = [["SCHEMA", "1"], ["GUARDS", identifier, "True", "True", "True"],
            ["DOCUMENT", identifier, "17", source, target]]
    token = 0
    for paragraph, position in enumerate((0.8, 0.5, 0.2)):
        for mode in ("original", "restored"):
            for stage in ("before", "after"):
                token += 1
                translated = (mode == "original") == (stage == "before")
                rows.append(["SAMPLE", identifier, str(position), mode, stage, "17", str(paragraph), "5", "True", "5",
                             "captured" if stage == "before" else "restored", "0", str(translated), "True",
                             target if translated else source, str(token), "True", source])
    rows += [["MANUAL_SCROLL", identifier, "0", "100"], ["STATUS", identifier, "COLLECTED"]]
    journal = "\t".join(["CLOSEUP_BATCH", identifier, source, source, target, "False"])
    return rows, journal, [identifier]


class DocumentVerifierTests(unittest.TestCase):
    def check(self, mutate=None):
        rows, journal, identifiers = fixture()
        if mutate:
            mutate(rows)
        return module.analyze("\n".join("\t".join(r) for r in rows), journal, identifiers)

    def test_complete_unit_fixture(self):
        self.assertTrue(self.check()["passed"])

    def test_rejects_missing_position(self):
        self.assertFalse(self.check(lambda rows: rows.pop(3))["passed"])

    def test_rejects_wrong_body_or_paragraph(self):
        for column, value in ((5, "99"), (6, "99"), (16, "False"), (17, enc("other source"))):
            with self.subTest(column=column):
                self.assertFalse(self.check(lambda rows: rows[4].__setitem__(column, value))["passed"])

    def test_rejects_stale_completion(self):
        self.assertFalse(self.check(lambda rows: rows[4].__setitem__(15, rows[3][15]))["passed"])

    def test_rejects_nan_and_geometry_drift(self):
        for value in ("nan", "10"):
            with self.subTest(value=value):
                self.assertFalse(self.check(lambda rows: rows[4].__setitem__(9, value))["passed"])

    def test_rejects_wrong_f8_text(self):
        self.assertFalse(self.check(lambda rows: rows[4].__setitem__(14, enc("wrong text")))["passed"])

    def test_rejects_scroll_lock_or_inactive_body(self):
        self.assertFalse(self.check(lambda rows: rows[-2].__setitem__(3, "0"))["passed"])
        self.assertFalse(self.check(lambda rows: rows[4].__setitem__(13, "False"))["passed"])

    def test_rejects_failed_guard_or_status(self):
        self.assertFalse(self.check(lambda rows: rows[1].__setitem__(2, "False"))["passed"])
        self.assertFalse(self.check(lambda rows: rows[-1].__setitem__(2, "FAILED"))["passed"])


if __name__ == "__main__":
    unittest.main()
