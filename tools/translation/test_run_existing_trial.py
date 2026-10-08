"""回归验证 CLI 空跑、漏行和没有真实调用时不能被当成试译通过。"""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from run_existing_trial import execution_options, merge_batch_results, qwen_translation_options, trial_complete, validate_batch


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

    def test_trial_config_isolated_budget_and_explicit_override(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            (trial / "trial-config.json").write_text(json.dumps({"budget_cny": 1, "lines": 30, "max_posts": 100}), encoding="utf-8")
            options = execution_options(SimpleNamespace(lines=20), trial)
            self.assertEqual(options, {"budget_cny": 1, "lines": 20, "max_posts": 100, "max_output_tokens": 4096})
            self.assertEqual(execution_options(SimpleNamespace(), trial)["budget_cny"], 1)
            for value in (0, -1, float("nan"), float("inf")):
                with self.assertRaises(ValueError):
                    execution_options(SimpleNamespace(budget_cny=value), trial)

    def test_mt_terms_are_native_and_domain_context_must_be_english(self):
        options = qwen_translation_options({"prompt_dictionary_data": [{"src": "Hamlet", "dst": "哈姆雷特", "info": "暂定"}],
                                           "qwen_mt_domains": "Hamlet is speaking to Ophelia."})
        self.assertEqual(options["terms"], [{"source": "Hamlet", "target": "哈姆雷特"}])
        self.assertIn("Hamlet is speaking", options["domains"])
        self.assertNotIn("暂定", options["domains"])
        with self.assertRaises(ValueError):
            qwen_translation_options({"qwen_mt_domains": "中文背景"})

    def test_controlled_stop_merges_unvisited_old_results_and_is_not_complete(self):
        manifest = {"batches": [{"id": key} for key in ("first", "second", "third")]}
        first = {"batch": "first", "exit_code": 0, "validation": {"passed": True}}
        second_failed = {"batch": "second", "exit_code": 1, "validation": {"passed": False}}
        third = {"batch": "third", "exit_code": 0, "validation": {"passed": True}}
        merged = merge_batch_results({"batches": [second_failed, third]}, [first], manifest)
        self.assertEqual(merged, [first, second_failed, third])
        self.assertFalse(trial_complete({"batches": merged}, manifest))
        partial = merge_batch_results(None, [first], manifest)
        self.assertEqual(partial, [first])
        self.assertFalse(trial_complete({"batches": partial}, manifest))


if __name__ == "__main__":
    unittest.main()
