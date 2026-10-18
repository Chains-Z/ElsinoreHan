"""阅读稿后续校订的来源与双源覆盖保护回归。"""

import unittest

from prepare_all_endings_followup import apply_reading_followup, paragraph_overrides
from prepare_dialogue_log_followup import digest


class ReadingFollowupTests(unittest.TestCase):
    def entry(self, source, previous, target):
        return {"source": source, "source_sha256": digest(source), "previous_target": previous,
                "target": target, "origins": ["绑定的结局源"]}

    def test_resource_and_compiled_sources_keep_separate_old_values(self):
        original = {"source": "raw -- source", "runtime_source": "raw—source",
                    "resource_target": "资源旧译", "target": "编译旧译"}
        entries = [self.entry("raw -- source", "资源旧译", "统一新译"),
                   self.entry("raw—source", "编译旧译", "统一新译")]
        used = set()
        actual = apply_reading_followup(original, paragraph_overrides(entries), used)
        self.assertEqual((actual["resource_target"], actual["target"]), ("统一新译", "统一新译"))
        self.assertEqual(used, {"raw -- source", "raw—source"})
        self.assertEqual(original["target"], "编译旧译")

    def test_no_implicit_fallback_to_other_variant(self):
        original = {"source": "raw -- source", "runtime_source": "raw—source",
                    "resource_target": "资源旧译", "target": "编译旧译"}
        actual = apply_reading_followup(original, paragraph_overrides([
            self.entry("raw -- source", "资源旧译", "资源新译")]), set())
        self.assertEqual(actual["target"], "编译旧译")

    def test_reject_wrong_old_value(self):
        original = {"source": "source", "runtime_source": "source",
                    "resource_target": "旧译", "target": "旧译"}
        with self.assertRaises(ValueError):
            apply_reading_followup(original, paragraph_overrides([
                self.entry("source", "不匹配的旧译", "新译")]), set())

    def test_reject_duplicate_source_wrong_hash_and_missing_origin(self):
        entry = self.entry("source", "旧译", "新译")
        for entries in ([entry, entry], [{**entry, "source_sha256": "0" * 64}],
                        [{**entry, "origins": []}]):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                paragraph_overrides(entries)


if __name__ == "__main__":
    unittest.main()
