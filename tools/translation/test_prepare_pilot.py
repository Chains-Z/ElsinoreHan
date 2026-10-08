"""检验试译样本的转义、注释和来源追溯，防止污染真实原文。"""

import unittest

from prepare_pilot import choose_scene_groups, decode_dialogue, mask_comments, read_dialogues


class PilotExtractionTests(unittest.TestCase):
    def test_escaped_backslash_does_not_become_newline(self):
        self.assertEqual(decode_dialogue(r"a\\nb\nc\q"), "a\\nb\nc\\q")

    def test_comments_keep_line_numbers_and_urls(self):
        body = '{Scene}\n/*\nophelia: "fake"\n*/\nophelia: "https://example.com" // note\n'
        self.assertEqual(mask_comments(body).count("\n"), body.count("\n"))
        rows = read_dialogues(body, "a" * 64, {"ophelia": "Ophelia"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_line"], 5)
        self.assertEqual(rows[0]["message"], "https://example.com")

    def test_only_character_dialogue_is_selected(self):
        body = '{Scene}\n[PlayMusic("technical")]\nophelia: [sad] {Sigh} "<i>No</i>!"\n'
        rows = read_dialogues(body, "b" * 64, {})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["message"], "<i>No</i>!")
        self.assertEqual(rows[0]["acting_cues"], "[sad] {Sigh}")

    def test_selection_finishes_whole_scene(self):
        rows = [{"scene": scene} for scene in ["helper", "Spine_OpheliaAloneStarter",
                "Spine_OpheliaAloneStarter", "second", "second", "third"]]
        self.assertEqual(len(choose_scene_groups(rows, 3)), 4)


if __name__ == "__main__":
    unittest.main()
