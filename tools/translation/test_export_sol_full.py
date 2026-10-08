"""检验动态提示按键与重排参数契约，实际格式再由XUnity解析器核对。"""

import unittest
import hashlib
from export_sol_full import apply_supplemental, encode, format_rule, printf_rule


class DynamicFormatTests(unittest.TestCase):
    def test_real_future_event_printf_template(self):
        result = printf_rule("<b>Ophelia</b> learns about an event in which %s", "<b>奥菲莉娅</b>得知了一个事件：%s")
        self.assertIn("${arg0}", result["replacement"])
        self.assertIn("{0}", result["format_source"])

    def test_noncurrent_option_is_added_without_changing_base(self):
        source = "Faster"
        entry = {"id": "settings-faster", "source": source, "target": "较快", "origins": ["真实设置显示方法"], "source_sha256": hashlib.sha256(source.encode()).hexdigest()}
        base = [{"id": "normal", "source": "Normal", "target": "普通"}]
        result = apply_supplemental(base, [entry])
        self.assertEqual([row["source"] for row in result], ["Normal", "Faster"])
        self.assertEqual(base[0]["target"], "普通")

    def test_existing_option_requires_recorded_previous_translation(self):
        entry = {"id": "settings-normal", "source": "Normal", "target": "正常", "origins": ["真实设置显示方法"], "source_sha256": hashlib.sha256(b"Normal").hexdigest()}
        with self.assertRaises(ValueError):
            apply_supplemental([{"id": "normal", "source": "Normal", "target": "普通"}], [entry])
        entry["previous_target"] = "普通"
        self.assertEqual(apply_supplemental([{"id": "normal", "source": "Normal", "target": "普通"}], [entry])[0]["target"], "正常")

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
