"""验证日志补修只消费真实短名、完整对白源和八块结构。"""

import json
from pathlib import Path
import unittest

from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, dialogue_source, digest, make_rules, short_name


class DialogueLogFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=json.loads((ROOT / "analysis/ui-audit/dialogue-log-source-audit.json").read_text(encoding="utf-8"))
        cls.cases=json.loads((ROOT / "translation/supplemental/dialogue-log-followup-tests.json").read_text(encoding="utf-8"))
        cls.rules=json.loads((ROOT / "translation/supplemental/dialogue-log-followup-rules.json").read_text(encoding="utf-8"))

    def test_real_shortname_second_word_contract(self):
        self.assertEqual(short_name("soldier",{"soldier":"Foreign Soldier"}),"Soldier")
        self.assertEqual(short_name("simona",{"simona":"Old Woman"}),"Woman")
        self.assertEqual(short_name("rosencrantz",{}),"Rosie")
        self.assertEqual(short_name("guildenstern",{}),"Guilda")

    def test_real_compiler_dash_and_ghost_italic(self):
        self.assertEqual(dialogue_source("ghost","No--"),"<i>No—</i>")
        self.assertEqual(dialogue_source("claudius","Yes -- bring him here"),"Yes—bring him here")

    def test_supplemental_variants_keep_frozen_targets(self):
        rows=json.loads((ROOT / "translation/supplemental/dialogue-log-runtime-aliases.json").read_text(encoding="utf-8"))
        base={r["id"]:r for r in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        self.assertEqual(len(rows),5)
        for row in rows:
            original=base[row["existing_id"]]
            self.assertEqual(row["target"],original["target"])
            self.assertEqual(row["source_sha256"],digest(row["source"]))
            self.assertEqual(row["existing_source_sha256"],digest(original["source"]))

    def test_four_unknown_name_words_only_in_speaker_labels(self):
        rules=[r for r in self.rules if r["id"].startswith("ui-rule-log-shortname-label-")]
        self.assertEqual(len(rules),4)
        for r in rules:
            self.assertIn(":</b> <indent=16%>",r["pattern"])
            self.assertIn("${body}",r["replacement"])
        self.assertEqual(set(SPECIAL_NAMES),{"Ghost","Figure","Woman","Grace"})

    def test_eight_blocks_keep_independent_captures(self):
        r=next(r for r in self.rules if r["id"]=="ui-rule-log-speaker-eight-blocks")
        for i in range(1,9):
            self.assertIn("(?<part"+str(i)+">",r["pattern"])
            self.assertIn("${part"+str(i)+"}",r["replacement"])
            self.assertIn("${boundary"+str(i)+"_i}",r["replacement"])
        self.assertIn("${rest}",r["replacement"])

    def test_full_sources_have_hashes_and_complete_scene_records(self):
        self.assertEqual(len(self.audit["source_assets"]),3)
        self.assertEqual(self.audit["parsed_dialogue_occurrences"],11554)
        self.assertEqual(self.audit["longest_same_actor_run"],37)
        for r in self.audit["dialogues"]:
            self.assertEqual(r["source_sha256"],digest(r["source"]))
            self.assertTrue(r["origin"]["scene"])
            self.assertGreater(r["origin"]["line"],0)

    def test_screenshots_and_unknown_rejection_are_present(self):
        self.assertEqual({r["id"] for r in self.cases if r["category"]=="screenshot"},
                         {"dialogue-log-screenshot-dinner","dialogue-log-screenshot-court"})
        self.assertEqual(len([r for r in self.cases if r["target"] is None]),7)
        self.assertNotIn("depth_stress",{r["category"] for r in self.cases})


if __name__ == "__main__":
    unittest.main()
