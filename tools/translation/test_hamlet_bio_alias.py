"""核对截图中 Hamlet 简介运行变体及冻结译文复用；仅最低层组件回归。"""

import hashlib
import json
from pathlib import Path
import unittest

from export_sol_full import apply_supplemental


ROOT = Path(__file__).resolve().parents[2]


class HamletBioAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads((ROOT / "translation/supplemental/hamlet-bio-alias.json").read_text(encoding="utf-8"))
        cls.alias = cls.entries[0]
        rows = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        cls.original = next(row for row in rows if row["id"] == "p00031-4dfce554591f")
        cls.evidence = json.loads((ROOT / "analysis/ui-audit/hamlet-bio-alias-evidence.json").read_text(encoding="utf-8"))

    def test_exact_runtime_source_from_real_ordered_replacements(self):
        source = self.original["source"]
        hits = []
        for old in [" -- ", " --- ", " - ", "-- ", "--- ", " --", " ---", "--", "---"]:
            hits.append(source.count(old))
            source = source.replace(old, "—")
        self.assertEqual(hits, [0, 0, 0, 0, 0, 0, 0, 1, 0])
        self.assertEqual(source, self.alias["source"])
        self.assertEqual(source, self.evidence["runtime_source"])
        self.assertEqual(len(self.original["source"]), 217)
        self.assertEqual(len(source), 216)
        self.assertTrue(source.endswith("but he's changed—and not for the better."))

    def test_target_reuses_frozen_translation_and_source_hashes(self):
        self.assertEqual(self.alias["target"], self.original["target"])
        self.assertEqual(self.alias["existing_id"], self.original["id"])
        self.assertEqual(self.alias["existing_source"], self.original["source"])
        for value, key in [(self.alias["source"], "source_sha256"),
                           (self.original["source"], "existing_source_sha256"),
                           (self.original["target"], "existing_target_sha256")]:
            self.assertEqual(hashlib.sha256(value.encode("utf-8")).hexdigest(), self.alias[key])

    def test_exact_dictionary_lookup_reproduces_miss_and_consumes_alias(self):
        dictionary = {self.original["source"]: self.original["target"]}
        self.assertNotIn(self.alias["source"], dictionary)
        dictionary[self.alias["source"]] = self.alias["target"]
        self.assertEqual(dictionary[self.alias["source"]], self.original["target"])
        self.assertNotIn(self.alias["source"].replace("Hamlet recently", "Hamlet has recently", 1), dictionary)

    def test_alias_satisfies_supplemental_contract_without_editing_original(self):
        base = [dict(self.original)]
        result = apply_supplemental(base, self.entries)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], self.original)
        self.assertEqual(result[1]["source"], self.alias["source"])
        self.assertEqual(result[1]["target"], self.original["target"])
        self.assertEqual(base[0], self.original)


if __name__ == "__main__":
    unittest.main()
