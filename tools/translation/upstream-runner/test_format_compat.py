"""拒绝结构不全的格式修复，核实只增加包装且选最后源文。"""

import unittest

from format_compat import wrap_complete_numbered_translation


class FormatCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.body = {"messages": [{"role": "user", "content":
            "系统示例：<textarea>\n1.示例\n</textarea>\n真正源文：<textarea>\n1.Hello\n2.World\n</textarea>"}]}

    def test_only_wrapper_added_and_last_source_selected(self):
        raw = "1.[甲]你好。\n2.[乙]<i>世界</i>。"
        result, note = wrap_complete_numbered_translation(raw, self.body)
        self.assertEqual(result, "<textarea>\n" + raw + "\n</textarea>")
        self.assertEqual(note["matched_numbers"], [1, 2])

    def test_incomplete_duplicate_reordered_empty_or_explained_rejected(self):
        for raw in ("1.你好", "1.你好\n1.世界", "2.世界\n1.你好", "1.你好\n2. ",
                    "译文如下：\n1.你好\n2.世界", "1.你好\n2.世界\n说明完毕", "1.你好\n\n2.世界",
                    "1.你好\n2.[角色]", "```\n1.你好\n2.世界\n```"):
            result, note = wrap_complete_numbered_translation(raw, self.body)
            self.assertEqual(result, raw)
            self.assertIsNone(note)


if __name__ == "__main__":
    unittest.main()
