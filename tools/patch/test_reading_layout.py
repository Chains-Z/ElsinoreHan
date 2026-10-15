"""排版报告判定器的局部异常回归，模拟报告不冒充真实UI验收。"""

import base64
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("reading_layout", Path(__file__).with_name("verify-reading-layout.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
enc = lambda value: base64.b64encode(value.encode()).decode()
render = lambda rows: "\n".join("\t".join(row) for row in rows)


def speaker_fixture():
    cases = "0\t" + enc("Source") + "\t" + enc("译文")
    rows = [["SCHEMA", "1"]]
    for width in ("1", "0.72"):
        for phase in ("translated", "original", "restored"):
            rows.append(["SAMPLE", "0", width, phase, "1000", "36", "36", "200", "210", "0", "0", "123",
                         enc("Source" if phase == "original" else "译文")])
    return rows + [["STATUS", "COLLECTED"]], cases


def biography_fixture():
    rows = [["SCHEMA", "1"]]
    for name in ("middle", "bottom", "manual-away"):
        for leg in ("0", "1"):
            for stage in ("before", "after"):
                translated = (leg == "0") == (stage == "before")
                bottom = name == "bottom"
                outcome = "captured" if stage == "before" else "bottom-restored" if bottom else "restored"
                rows.append(["SAMPLE", "brit", name, leg, stage, "123", "1" if stage == "before" else "2", "True", "0", "0", "True", "0",
                    outcome, "0", str(bottom), "0" if bottom else "0.35" if name == "manual-away" else "0.5", "100",
                    enc("Source"), enc("译文"), enc("译文" if translated else "Source"), enc("Source")])
    return rows + [["STATUS", "COLLECTED"]], "BUILDER\tcharacter:brit\t" + enc("Source")


class ReadingLayoutTests(unittest.TestCase):
    def test_valid_reports(self):
        speakers, cases = speaker_fixture()
        biographies, journal = biography_fixture()
        self.assertTrue(MODULE.analyze_speakers(render(speakers), cases)["passed"])
        self.assertTrue(MODULE.analyze_biographies(render(biographies), journal)["passed"])

    def test_overlap_rejected(self):
        rows, cases = speaker_fixture()
        rows[1][8] = "195"
        self.assertFalse(MODULE.analyze_speakers(render(rows), cases)["passed"])

    def test_font_shrink_rejected(self):
        rows, cases = speaker_fixture()
        rows[1][6] = "24"
        self.assertFalse(MODULE.analyze_speakers(render(rows), cases)["passed"])

    def test_original_text_mutation_rejected(self):
        rows, cases = speaker_fixture()
        rows[2][12] = enc("Rewritten source")
        self.assertFalse(MODULE.analyze_speakers(render(rows), cases)["passed"])

    def test_stale_anchor_rejected(self):
        rows, journal = biography_fixture()
        rows[2][6] = "1"
        self.assertFalse(MODULE.analyze_biographies(render(rows), journal)["passed"])

    def test_wrong_paragraph_rejected(self):
        rows, journal = biography_fixture()
        rows[2][8] = "1"
        self.assertFalse(MODULE.analyze_biographies(render(rows), journal)["passed"])

    def test_business_source_mutation_rejected(self):
        rows, journal = biography_fixture()
        rows[2][20] = enc("中文写回业务")
        self.assertFalse(MODULE.analyze_biographies(render(rows), journal)["passed"])

    def test_bottom_claim_with_drift_rejected(self):
        rows, journal = biography_fixture()
        next(row for row in rows if row[:5] == ["SAMPLE", "brit", "bottom", "0", "after"])[15] = "0.3"
        self.assertFalse(MODULE.analyze_biographies(render(rows), journal)["passed"])

    def test_missing_portrait_rejected(self):
        rows, journal = biography_fixture()
        journal += "\nBUILDER\tcharacter:hamlet\t" + enc("Another source")
        self.assertFalse(MODULE.analyze_biographies(render(rows), journal)["passed"])


if __name__ == "__main__":
    unittest.main()
