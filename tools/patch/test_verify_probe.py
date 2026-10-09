"""对已发现的误判分支做局部回归，不替代真实游戏验收。"""

import unittest
import base64
import importlib.util
import json
from pathlib import Path

specification = importlib.util.spec_from_file_location("verify_probe", Path(__file__).with_name("verify-probe.py"))
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)
evaluate = module.evaluate


def visible(text: str, overflow: bool = False) -> dict:
    return {"active": True, "text": text, "overflow": overflow}


class ProbeRegressionTests(unittest.TestCase):
    def test_background_input_guard_cannot_claim_partial_isolation(self):
        for report in ("PHYSICAL_INPUT_GUARD_ACTIVE=False BLOCKED=0\nPHYSICAL_INPUT_MODULES_DISABLED=1",
                       "PHYSICAL_INPUT_GUARD_ACTIVE=True BLOCKED=12\nPHYSICAL_INPUT_MODULES_DISABLED=0"):
            with self.subTest(report=report):
                self.assertFalse(evaluate([], [], report, "")["headless_cancel_and_submit_input_isolated"])

    def test_background_input_guard_requires_controller_and_module_isolation(self):
        report = "PHYSICAL_INPUT_GUARD_ACTIVE=True BLOCKED=12\nPHYSICAL_INPUT_MODULES_DISABLED=1"
        self.assertTrue(evaluate([], [], report, "")["headless_cancel_and_submit_input_isolated"])

    def test_journal_navigation_omits_unvisited_settings_without_claiming_pass(self):
        result = evaluate([visible("继续游戏"), visible("设置"), visible("退出游戏")], [],
                          "GLYPHS_继续游戏设置退出=True", "", include_settings=False)
        self.assertTrue(all(result.values()))
        self.assertFalse(any(key.startswith("settings_") for key in result))

    def test_only_current_settings_values_are_insufficient(self):
        report = "STATUS\tCOMPLETE\nCANCELLED\tTrue\nSCOPES_RETAINED\tTrue\n"
        result = module.evaluate_settings_options(report, {"Faster": "较快"})
        self.assertFalse(result["settings_all_noncurrent_options_visited"])
        self.assertFalse(result["settings_all_option_values_translated"])

    def test_untranslated_faster_is_rejected_even_when_every_option_visited(self):
        options = {"TextSpeed": ["Normal", "Faster", "Fastest", "Instant"], "AlternateCostumes": ["Default", "Modern"],
                   "Quality": ["Low", "Medium", "High"], "ScreenMode": ["Windowed", "Borderless", "Fullscreen"], "Resolution": ["Native"]}
        translations = {s: "中文" for values in options.values() for s in values}
        encode = lambda s: base64.b64encode(s.encode()).decode()
        lines = ["STATUS\tCOMPLETE", "CANCELLED\tTrue", "SCOPES_RETAINED\tTrue"]
        for slot, values in options.items():
            for index, source in enumerate(values):
                target = source if source == "Faster" else translations[source]
                lines.append("\t".join(["OPTION", slot, str(index), encode(source), encode(target), "translated", "False", "True"]))
        result = module.evaluate_settings_options("\n".join(lines), translations)
        self.assertTrue(result["settings_all_noncurrent_options_visited"])
        self.assertFalse(result["settings_all_option_values_translated"])
        self.assertFalse(result["settings_each_slot_toggle_original"])

    def test_original_complete_labels_do_not_pass_abbreviated_dictionary(self):
        result = evaluate([visible("Continue Game"), visible("设置"), visible("Quit Game")], [], "", "")
        self.assertFalse(result["menu_labels_all_translated"])
        self.assertFalse(result["menu_no_original_labels"])

    def test_unopened_settings_cannot_pass_overflow_check(self):
        result = evaluate([], [visible("设置")], "", "")
        self.assertFalse(result["settings_page_opened"])
        self.assertFalse(result["settings_visible_texts_no_overflow"])

    def test_inactive_expected_texts_do_not_count(self):
        items = [{"active": False, "text": text, "overflow": False} for text in ("继续游戏", "设置", "退出游戏")]
        result = evaluate(items, [], "", "")
        self.assertFalse(result["menu_labels_all_translated"])
        self.assertFalse(result["menu_labels_no_overflow"])

    def test_open_settings_overflow_is_reported(self):
        result = evaluate([], [visible("Graphics"), visible("Audio"), visible("Gameplay"), visible("Resolution", True)], "", "EventSystem")
        self.assertTrue(result["settings_page_opened"])
        self.assertFalse(result["settings_visible_texts_no_overflow"])

    def test_new_game_menu_is_valid_alternative(self):
        result = evaluate([visible("开始新游戏"), visible("设置"), visible("退出游戏")], [], "", "")
        self.assertTrue(result["menu_labels_all_translated"])
        self.assertTrue(result["menu_labels_no_overflow"])

    def test_start_prologue_uses_exact_frozen_translation(self):
        root = Path(__file__).resolve().parents[2]
        rows = json.loads((root / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        self.assertEqual(next(row["target"] for row in rows if row["source"] == "Start Prologue"), "开始序章")

    def test_start_prologue_menu_is_valid_alternative(self):
        result = evaluate([visible("开始序章"), visible("设置"), visible("退出游戏")], [],
                          "GLYPHS_继续游戏设置退出=True", "", include_settings=False)
        self.assertTrue(all(result.values()))

    def test_start_prologue_overflow_is_rejected(self):
        result = evaluate([visible("开始序章", True), visible("设置"), visible("退出游戏")], [], "", "")
        self.assertTrue(result["menu_labels_all_translated"])
        self.assertFalse(result["menu_labels_no_overflow"])

    def test_untranslated_start_prologue_menu_is_rejected(self):
        result = evaluate([visible("Start Prologue"), visible("设置"), visible("退出游戏")], [], "", "")
        self.assertFalse(result["menu_labels_all_translated"])
        self.assertFalse(result["menu_no_original_labels"])

    def test_remaining_english_prologue_is_rejected_even_with_chinese_entry(self):
        result = evaluate([visible("开始序章"), visible("Start Prologue"), visible("设置"), visible("退出游戏")], [], "", "")
        self.assertFalse(result["menu_no_original_labels"])

    def test_menu_without_start_label_does_not_pass(self):
        self.assertFalse(evaluate([visible("设置"), visible("退出游戏")], [], "", "")["menu_labels_all_translated"])

    def test_generic_eventsystem_log_is_not_navigation_proof(self):
        self.assertFalse(evaluate([], [], "", "EventSystem loaded")["settings_pointer_navigation_logged"])
        self.assertTrue(evaluate([], [], "", "已通过真实设置按钮的 EventSystem 指针事件打开设置界面")["settings_pointer_navigation_logged"])

    def test_real_options_source_is_valid_toggle_original(self):
        result = module.evaluate_toggle({"Options", "Quit Game", "Continue Game"}, {"设置", "退出游戏", "继续游戏"}, "F8_RELEASE_NO_CHANGE=True")
        self.assertTrue(all(result.values()))

    def test_remaining_chinese_is_not_original_toggle(self):
        result = module.evaluate_toggle({"Options", "Quit Game", "Continue Game", "设置"}, {"设置", "退出游戏", "继续游戏"}, "")
        self.assertFalse(result["toggle_original_menu"])

    def test_start_prologue_toggle_original_and_restored_are_valid(self):
        for options in ("Options", "Settings"):
            with self.subTest(options=options):
                result = module.evaluate_toggle({options, "Quit Game", "Start Prologue"},
                                                {"设置", "退出游戏", "开始序章"}, "F8_RELEASE_NO_CHANGE=True")
                self.assertTrue(all(result.values()))

    def test_remaining_chinese_prologue_is_not_original_toggle(self):
        result = module.evaluate_toggle({"Options", "Quit Game", "Start Prologue", "开始序章"},
                                        {"设置", "退出游戏", "开始序章"}, "F8_RELEASE_NO_CHANGE=True")
        self.assertFalse(result["toggle_original_menu"])

    def test_untranslated_prologue_is_not_restored_toggle(self):
        result = module.evaluate_toggle({"Options", "Quit Game", "Start Prologue"},
                                        {"设置", "退出游戏", "Start Prologue"}, "F8_RELEASE_NO_CHANGE=True")
        self.assertFalse(result["toggle_restored_menu"])


if __name__ == "__main__":
    unittest.main()
