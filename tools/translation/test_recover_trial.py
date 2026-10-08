"""验证冻结果恢复的格式和源文对齐，防止漏行与额外解释被吞掉。"""

import json
import unittest

from recover_trial import numbered_rows, restore_batch


class FrozenRecoveryTests(unittest.TestCase):
    def test_bare_numbered_rows_are_preserved(self):
        self.assertEqual(numbered_rows("1.[Ophelia]不。\n2.午夜。"), [(1, "[Ophelia]不。"), (2, "午夜。")])

    def test_duplicate_missing_or_explanation_is_rejected(self):
        for content in ["1.不。\n1.是。", "2.不。", "译文如下：\n1.不。"]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                numbered_rows(content)

    def test_source_must_match_exactly(self):
        events = [{"event": "started", "request_index": 1,
                   "request_body": {"messages": [{"content": "<textarea>\n1.Yes.\n</textarea>"}]}},
                  {"event": "completed", "request_index": 1, "status_code": 200, "model": "test",
                   "response_body": json.dumps({"choices": [{"message": {"content": "1.是。"}}]})}]
        with self.assertRaises(ValueError):
            restore_batch([{"message": "No."}], events, "test")

    def test_native_mt_recovers_only_exact_numbered_source(self):
        model = "qwen-mt-plus"
        events = [{"event": "started", "request_index": 1,
                   "request_body": {"model": model, "translation_options": {"source_lang": "English", "target_lang": "Chinese"},
                                    "messages": [{"role": "user", "content": "1.[Hamlet]No."}]}},
                  {"event": "completed", "request_index": 1, "status_code": 200, "model": model,
                   "response_body": json.dumps({"choices": [{"message": {"content": "1.[Hamlet]不。"}}]})}]
        restored, used = restore_batch([{"name": "Hamlet", "message": "No."}], events, model)
        self.assertEqual(restored, [{"name": "Hamlet", "message": "不。"}])
        self.assertEqual(used, [1])
        with self.assertRaises(ValueError):
            restore_batch([{"name": "Hamlet", "message": "Yes."}], events, model)


if __name__ == "__main__":
    unittest.main()
