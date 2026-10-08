"""检验动态提示按键与重排参数契约，实际格式再由XUnity解析器核对。"""

import unittest
from export_sol_full import encode, format_rule


class DynamicFormatTests(unittest.TestCase):
    def test_tutorial_keys_are_not_translated(self):
        result = format_rule("Try pressing {0} to open it.", "试着按{0}打开。")
        self.assertTrue(result["preserve_args"])
        self.assertIn("${arg0_i}", result["replacement"])

    def test_history_arguments_may_reorder(self):
        result = format_rule("Ophelia presents {0} to {1}.", "奥菲莉娅向{1}出示{0}。")
        self.assertFalse(result["preserve_args"])
        self.assertEqual(result["replacement"], "奥菲莉娅向${arg1}出示${arg0}。")

    def test_variable_only_source_cannot_match_every_text(self):
        self.assertIsNone(format_rule("{0}", "{0}"))

    def test_comments_and_equals_escape(self):
        self.assertEqual(encode("A=B//C"), "A\\=B\\u002f\\u002fC")

    def test_splitter_preserves_literal_dollar(self):
        result = format_rule("The payment is ${0} today.", "今天支付${0}。")
        self.assertEqual(result["replacement"], "今天支付$${arg0}。")


if __name__ == "__main__":
    unittest.main()
