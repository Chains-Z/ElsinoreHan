"""检查 Sol 译文完整性门槛，防止漏条和标签破坏进入词表。"""

import unittest
import hashlib
from run_sol_full import validate


class SolOutputTests(unittest.TestCase):
    def test_complete_translation_passes(self):
        self.assertEqual(validate([{"id": "a", "source": "I <i>know</i>."}],
                                  {"translations": [{"id": "a", "target": "我<i>知道</i>。"}]}), [])

    def test_missing_and_duplicate_rows_fail(self):
        source = [{"id": "a", "source": "One"}, {"id": "b", "source": "Two"}]
        self.assertTrue(validate(source, {"translations": [{"id": "a", "target": "一"}]}))
        self.assertTrue(validate(source, {"translations": [{"id": "a", "target": "一"}, {"id": "a", "target": "二"}]}))

    def test_lost_variable_and_tag_fail(self):
        source = [{"id": "a", "source": "Hello {0}, <b>wait</b>"}]
        self.assertTrue(validate(source, {"translations": [{"id": "a", "target": "你好，等一下"}]}))

    def test_untranslated_sentence_fails(self):
        self.assertTrue(validate([{"id": "a", "source": "My father died."}],
                                 {"translations": [{"id": "a", "target": "My father died."}]}))

    def test_real_braced_sentence_is_body_not_placeholder(self):
        self.assertEqual(validate([{"id": "a", "source": "{It's... empty.}"}],
                                  {"translations": [{"id": "a", "target": "{里面……空了。}"}]}), [])

    def test_real_identifier_and_brace_wrapping_still_protected(self):
        self.assertTrue(validate([{"id": "a", "source": "Hello {player_name}."}],
                                 {"translations": [{"id": "a", "target": "你好{玩家名字}。"}]}))
        self.assertTrue(validate([{"id": "a", "source": "{It's... empty.}"}],
                                 {"translations": [{"id": "a", "target": "里面……空了。"}]}))

    def test_reviewed_nontext_requires_exact_source_hash(self):
        text = "sdffMIgjWt gfgdfgfgfgfgfg"
        source = [{"id": "a", "source": text}]
        value = {"translations": [{"id": "a", "target": text}]}
        exclusions = {"a": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        self.assertEqual(validate(source, value, exclusions), [])
        self.assertTrue(validate([{"id": "a", "source": "My father died."}], value, exclusions))


if __name__ == "__main__":
    unittest.main()
