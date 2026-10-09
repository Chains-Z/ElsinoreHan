"""检验动态提示按键与重排参数契约，实际格式再由XUnity解析器核对。"""

import unittest
import hashlib
import json
import re
from export_sol_full import ROOT, apply_supplemental, encode, format_rule, printf_rule, render_ui_rule


class DynamicFormatTests(unittest.TestCase):
    def test_backerbook_runtime_alias_follows_observed_compiler_contract(self):
        rows = json.loads((ROOT / "translation/supplemental/runtime-closeup-translations.json").read_text(encoding="utf-8"))
        translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 1)
        alias = rows[0]
        original = next(row for row in translations if row["id"] == alias["canonical_source_id"])
        expected = original["source"]
        for pattern in (" -- ", " --- ", " - ", "-- ", "--- ", " --", " ---", "--", "---"):
            expected = expected.replace(pattern, "—")
        self.assertEqual(alias["source"], expected)
        self.assertEqual(alias["target"], original["target"])
        self.assertEqual(hashlib.sha256(alias["source"].encode()).hexdigest(), alias["source_sha256"])

    def test_supplemental_layers_require_exact_previous_target_and_unique_source(self):
        source = "Open Journal"
        first = {"id": "first", "source": source, "target": "打开日志", "origins": ["真实菜单"],
                 "source_sha256": hashlib.sha256(source.encode()).hexdigest()}
        second = {**first, "id": "second", "target": "打开笔记", "previous_target": "打开日志"}
        initial = apply_supplemental([], [first])
        self.assertEqual(apply_supplemental(initial, [second])[0]["target"], "打开笔记")
        with self.assertRaises(ValueError):
            apply_supplemental([], [first, second])
        with self.assertRaises(ValueError):
            apply_supplemental(initial, [{**second, "previous_target": "错误旧值"}])

    def test_observed_history_fixture_hashes_and_visible_text(self):
        rows = json.loads((ROOT / "translation/supplemental/dynamic-ui-tests.json").read_text(encoding="utf-8"))
        observed = [row for row in rows if row["id"].startswith("log-observed-history-")]
        self.assertEqual([row["id"] for row in observed], ["log-observed-history-" + str(i) for i in range(4)])
        for row in observed:
            with self.subTest(id=row["id"]):
                self.assertEqual(row["verification_level"], "component")
                self.assertEqual(hashlib.sha256(row["source"].encode()).hexdigest(), row["source_sha256"])
                self.assertEqual(hashlib.sha256(row["target"].encode()).hexdigest(), row["target_sha256"])
                self.assertNotRegex(re.sub(r"<[^>]*>", "", row["target"]), r"[A-Za-z]")

    def test_real_log_continuation_padding_and_punctuation(self):
        rule = {"id": "ui-rule-log-frozen-continuation", "pattern": r"^(?<first>(?:Known dialogue))(?<newline_i>\n)(?<rest>[\s\S]+)\z$",
                "continuation_separator_padding": True, "continuation_punctuation": ["..."]}
        rendered = render_ui_rule(rule)
        self.assertIn(r"(?:Known dialogue)|\.\.\.)(?<newline_i>[ \t]*\n)", rendered["pattern"])
        self.assertNotEqual(rendered["pattern"], rule["pattern"])
        self.assertNotIn("|.*", rendered["pattern"])

    def test_continuation_options_reject_other_rules_or_unknown_punctuation(self):
        rule = {"id": "other", "pattern": r"^(?<first>x)(?<newline_i>\n)$", "continuation_separator_padding": True,
                "continuation_punctuation": ["..."]}
        with self.assertRaises(ValueError):
            render_ui_rule(rule)
        rule["id"] = "ui-rule-log-frozen-continuation"
        rule["continuation_punctuation"] = ["unknown-id"]
        with self.assertRaises(ValueError):
            render_ui_rule(rule)

    def test_continuation_requires_unique_exact_marker(self):
        rule = {"id": "ui-rule-log-frozen-continuation", "pattern": r"^x$", "continuation_separator_padding": True,
                "continuation_punctuation": ["..."]}
        with self.assertRaises(ValueError):
            render_ui_rule(rule)
        rule["pattern"] = r"^(?<first>x)(?<newline_i>\n)(?<first>y)(?<newline_i>\n)$"
        with self.assertRaises(ValueError):
            render_ui_rule(rule)

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
