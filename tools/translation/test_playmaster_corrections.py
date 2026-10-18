"""统一称号的来源、覆盖链和原文标记回归，不修改冻结模型响应。"""

import hashlib
import json
from pathlib import Path
import re
import unittest

from export_sol_full import apply_supplemental

ROOT = Path(__file__).resolve().parents[2]


class PlaymasterCorrectionsTests(unittest.TestCase):
    def test_all_known_occurrences_have_one_title(self):
        rows = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        related = [row for row in rows if re.search("playmaster", row["source"], re.I)]
        self.assertEqual(len(related), 33)
        for row in related:
            with self.subTest(row=row["id"]):
                self.assertIn("戏班班主", row["target"])
                self.assertNotRegex(row["target"], "戏剧大师|剧团团长|戏剧主宰|戏局之主|戏班主|戏剧之主|掌戏人")

    def test_corrections_require_original_source_and_previous_target(self):
        changes = json.loads((ROOT / "translation/supplemental/playmaster-corrections.json").read_text(encoding="utf-8"))
        for row in changes:
            self.assertTrue(re.search("playmaster", row["source"], re.I))
            self.assertEqual(hashlib.sha256(row["source"].encode()).hexdigest(), row["source_sha256"])
            with self.assertRaises(ValueError):
                apply_supplemental([{"id": "prior", "source": row["source"], "target": "错误的先前译文"}], [row])

    def test_emphasis_in_questions_and_dialogue_remains(self):
        rows = {row["id"]: row for row in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        self.assertIn("<i>戏班班主？</i>", rows["p04980-bc4c40ad16f3"]["target"])
        self.assertTrue(rows["a00605-462db6c9146f"]["target"].startswith("<i>"))
        self.assertTrue(rows["a00605-462db6c9146f"]["target"].endswith("</i>"))

    def test_runtime_alias_reuses_corrected_original(self):
        rows = {row["id"]: row for row in json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))}
        aliases = json.loads((ROOT / "translation/supplemental/lead-runtime-aliases.json").read_text(encoding="utf-8"))
        row = next(row for row in aliases if row["id"] == "ui-lead-runtime-421c4d7afde8f610")
        self.assertEqual(rows[row["id"]]["target"], rows[row["existing_id"]]["target"])
        self.assertEqual(hashlib.sha256(row["target"].encode()).hexdigest(), row["existing_target_sha256"])
