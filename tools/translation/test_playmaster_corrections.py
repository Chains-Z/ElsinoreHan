"""统一称号的来源、覆盖链和原文标记回归，不修改冻结模型响应。"""

import hashlib
import json
from pathlib import Path
import re
import unittest

from export_sol_full import apply_supplemental

ROOT = Path(__file__).resolve().parents[2]


class PlaymasterCorrectionsTests(unittest.TestCase):
    def test_extracted_player_sources_have_exact_dictionary_keys(self):
        sources = {row["source"] for row in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        counts = {}
        excluded = []
        for filename in ("resource-strings.json", "assembly-strings.json"):
            records = json.loads((ROOT / "analysis/ui-audit" / filename).read_text(encoding="utf-8"))
            related = [row for row in records if re.search(r"\bplaymaster\b", row["source"], re.I)]
            counts[filename] = len(related)
            for row in related:
                if row["source"] == "hasSeen(quince,Playmaster)":
                    excluded.append(row["source"])
                    continue
                self.assertTrue(row["source"] in sources or row["source"].strip() in sources, row["source"])
        self.assertEqual(counts, {"resource-strings.json": 12, "assembly-strings.json": 23})
        self.assertEqual(excluded, ["hasSeen(quince,Playmaster)"])

    def test_all_known_occurrences_have_one_title(self):
        rows = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        related = [row for row in rows if re.search("playmaster", row["source"], re.I)]
        self.assertEqual(len(related), 33)
        contextual = {"p05100-87aee950478d", "p05102-f48124a8429e", "p12952-77f621c7e989"}
        for row in related:
            with self.subTest(row=row["id"]):
                self.assertIn("艺人" if row["id"] in contextual else "戏剧大师", row["target"])
                self.assertNotRegex(row["target"], "戏班班主|剧团团长|戏剧主宰|戏局之主|戏班主|戏剧之主|掌戏人")

    def test_corrections_require_original_source_and_previous_target(self):
        changes = json.loads((ROOT / "translation/supplemental/playmaster-corrections.json").read_text(encoding="utf-8"))
        for row in changes:
            self.assertTrue(re.search("playmaster", row["source"], re.I))
            self.assertEqual(hashlib.sha256(row["source"].encode()).hexdigest(), row["source_sha256"])
            with self.assertRaises(ValueError):
                apply_supplemental([{"id": "prior", "source": row["source"], "target": "错误的先前译文"}], [row])

    def test_emphasis_in_questions_and_dialogue_remains(self):
        rows = {row["id"]: row for row in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        self.assertIn("<i>戏剧大师？</i>", rows["p04980-bc4c40ad16f3"]["target"])
        self.assertTrue(rows["a00605-462db6c9146f"]["target"].startswith("<i>"))
        self.assertTrue(rows["a00605-462db6c9146f"]["target"].endswith("</i>"))

    def test_runtime_alias_reuses_corrected_original(self):
        rows = {row["id"]: row for row in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        aliases = json.loads((ROOT / "translation/supplemental/lead-runtime-aliases.json").read_text(encoding="utf-8"))
        row = next(row for row in aliases if row["id"] == "ui-lead-runtime-421c4d7afde8f610")
        self.assertEqual(rows[row["id"]]["target"], rows[row["existing_id"]]["target"])
        self.assertEqual(hashlib.sha256(row["target"].encode()).hexdigest(), row["existing_target_sha256"])

    def test_contempt_and_teasing_follow_each_speakers_context(self):
        rows = {row["id"]: row for row in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        expected = {
            "p05100-87aee950478d": "彼得·昆斯？就那个乡下来的艺人？可我不明白！",
            "p05102-f48124a8429e": "彼得·昆斯？就那个乡下来的艺人？可我不明白。",
            "p12952-77f621c7e989": "昆斯……这名字耳熟。啊。你是说那个四处巡演的小艺人？",
            "p12957-6894bcf32761": "他这个戏剧大师，本来就是扮丑角的。他要是不古怪，岂不是连丑角都演不好了？",
            "p09035-d99b906cd95f": "那你呢，戏剧大师？你就坐在那儿，任由一群姑娘说你没用？",
        }
        for identifier, target in expected.items():
            with self.subTest(identifier=identifier):
                self.assertEqual(rows[identifier]["target"], target)
