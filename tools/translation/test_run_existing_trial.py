"""回归验证 CLI 空跑、漏行和没有真实调用时不能被当成试译通过。"""

import json
import tempfile
import unittest
from pathlib import Path

from run_existing_trial import trial_complete, validate_batch


class TrialCompletionTests(unittest.TestCase):
    def check(self, target, calls):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps([{"message": "No."}]), encoding="utf-8")
            output = root / "output"
            output.mkdir()
            (output / source.name).write_text(json.dumps(target), encoding="utf-8")
            return validate_batch(source, output, calls)

    def test_cli_zero_work_does_not_pass(self):
        self.assertFalse(self.check([{"message": "No."}], 0)["passed"])

    def test_chinese_without_real_call_does_not_pass(self):
        self.assertFalse(self.check([{"message": "不。"}], 0)["passed"])

    def test_missing_output_line_does_not_pass(self):
        self.assertFalse(self.check([], 1)["passed"])

    def test_real_call_and_complete_chinese_pass_structure(self):
        self.assertTrue(self.check([{"message": "不。"}], 1)["passed"])

    def test_passed_first_batch_can_resume_missing_batches(self):
        manifest = {"batches": [{"id": "first"}, {"id": "second"}]}
        previous = {"batches": [{"batch": "first", "exit_code": 0, "validation": {"passed": True}}]}
        self.assertFalse(trial_complete(previous, manifest))

    def test_all_expected_batches_prevent_duplicate_payment(self):
        manifest = {"batches": [{"id": "first"}, {"id": "second"}]}
        previous = {"batches": [{"batch": key, "exit_code": 0, "validation": {"passed": True}}
                                for key in ("first", "second")]}
        self.assertTrue(trial_complete(previous, manifest))


if __name__ == "__main__":
    unittest.main()
