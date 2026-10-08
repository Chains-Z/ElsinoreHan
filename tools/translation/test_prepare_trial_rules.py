"""回归检查没有说话人的真实资料可以进入规则配置。"""

import unittest

from prepare_trial_rules import source_with_speaker


class TrialRulesTests(unittest.TestCase):
    def test_none_speaker_for_information(self):
        self.assertEqual(source_with_speaker({"name": None, "message": "All"}), " All")

    def test_named_dialogue(self):
        self.assertEqual(source_with_speaker({"name": "Ophelia", "message": "No."}), "Ophelia No.")


if __name__ == "__main__":
    unittest.main()
