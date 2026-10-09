"""覆盖原先只验首段、三态空文本误通过等异常；夹具不是游戏E2E。"""

import base64
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("lead_verifier", Path(__file__).with_name("verify-lead-followup.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def enc(text):
    return base64.b64encode(text.encode()).decode()


class LeadVerifierTests(unittest.TestCase):
    def setUp(self):
        self.groups = {"1": [{"source": "First real paragraph.", "target": "第一段。"},
                              {"source": "Second real paragraph.", "target": "第二段。"}]}
        self.source = MODULE.PREFIX + "First real paragraph.\n\nSecond real paragraph."
        self.target = MODULE.PREFIX + "第一段。\n\n第二段。"

    def report(self, translated=None, restored=None, active=True):
        lines = ["EXPECTED_AVAILABLE\t1", "SOURCE\tavailable\tid\t" + enc(self.source),
                 "SOURCE\treplay\tcase\t" + enc(self.source), "EXPECTED\treplay\tcase\t" + enc(self.target)]
        for kind, name in (("available", "id"), ("replay", "case")):
            for mode, text in (("translated", self.target if translated is None else translated),
                               ("original", self.source), ("restored", self.target if restored is None else restored)):
                lines.append("\t".join(("TEXT", kind, name, mode, "1", str(active), enc(text))))
        return "\n".join(lines + ["STATUS\tCOMPLETE"])

    def test_complete_targets_pass(self):
        self.assertTrue(MODULE.analyze(self.report(), self.groups)["passed"])

    def test_first_paragraph_only_translated_fails(self):
        self.assertFalse(MODULE.analyze(self.report(translated=MODULE.PREFIX + "第一段。\n\nSecond real paragraph."), self.groups)["passed"])

    def test_matching_empty_translated_and_restored_fails(self):
        self.assertFalse(MODULE.analyze(self.report(translated="", restored=""), self.groups)["passed"])

    def test_inactive_component_fails(self):
        self.assertFalse(MODULE.analyze(self.report(active=False), self.groups)["passed"])

    def test_repeated_replay_cannot_replace_missing_case(self):
        report = self.report()
        sources = [line for line in report.splitlines() if line.startswith("SOURCE\treplay")]
        self.assertFalse(MODULE.analyze(report + "\n" + "\n".join(sources), self.groups)["passed"])

    def test_required_replay_cannot_be_omitted(self):
        self.assertFalse(MODULE.analyze(self.report(), self.groups, {"missing-required-case"})["passed"])

    def test_unknown_or_out_of_order_source_rejected(self):
        for source in ("First real paragraph.\n\nUnknown", "Second real paragraph.\n\nFirst real paragraph."):
            with self.subTest(source=source), self.assertRaises(ValueError):
                MODULE.expected_content(source, self.groups)

    def test_embedded_double_newline_is_not_mistaken_for_new_field(self):
        groups = {"1": [{"source": "First\n\ninside.", "target": "第一段内部。"},
                         {"source": "Second.", "target": "第二段。"}]}
        self.assertEqual(MODULE.expected_content("First\n\ninside.\n\nSecond.", groups), "第一段内部。\n\n第二段。")


if __name__ == "__main__":
    unittest.main()
