"""对已发现的误判分支做局部回归，不替代真实游戏验收。"""

import unittest
import importlib.util
from pathlib import Path

specification = importlib.util.spec_from_file_location("verify_probe", Path(__file__).with_name("verify-probe.py"))
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)
evaluate = module.evaluate


def visible(text: str, overflow: bool = False) -> dict:
    return {"active": True, "text": text, "overflow": overflow}


class ProbeRegressionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
