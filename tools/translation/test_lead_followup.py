"""验证真实线索来源与别名治理；格式组合由实际XUnity消费者另行验证。"""

import json
from pathlib import Path
import unittest

from export_sol_full import apply_supplemental
from prepare_lead_followup import build, runtime_source

ROOT = Path(__file__).resolve().parents[2]


class LeadFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = json.loads((ROOT / "analysis/ui-audit/resource-strings.json").read_text(encoding="utf-8-sig"))
        cls.translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
        cls.aliases, cls.rules, cls.cases, cls.groups = build(cls.resources, cls.translations)

    def test_all_resource_paragraphs_covered(self):
        self.assertEqual(len(self.groups), 20)
        self.assertEqual(sum(map(len, self.groups.values())), 136)
        self.assertEqual(len(self.aliases), 18)

    def test_chambers_screenshot_exact_dash_variant_is_added(self):
        alias = next(row for row in self.aliases if row["existing_id"] == "p00131-909b2d1ec2e1")
        self.assertIn("locked—but", alias["source"])
        self.assertEqual(alias["source"], runtime_source(alias["existing_source"]))

    def test_aliases_reuse_real_original_targets(self):
        originals = {row["id"]: row for row in self.translations}
        for alias in self.aliases:
            original = originals[alias["existing_id"]]
            result = apply_supplemental([original], [alias])
            self.assertEqual(result[-1]["target"], original["target"])
            with self.assertRaises(ValueError):
                apply_supplemental([original], [{**alias, "target": alias["target"] + "任意增写"}])

    def test_unknown_paragraph_fixture_has_no_target(self):
        unknown = [case for case in self.cases if case["id"].startswith("lead-unknown-")]
        self.assertEqual(len(unknown), 20)
        self.assertTrue(all(case["target"] is None for case in unknown))

    def test_reprepare_after_export_preserves_aliases(self):
        existing = {row["source"] for row in self.translations}
        merged = self.translations + [{key: row[key] for key in ("id", "source", "target")} for row in self.aliases if row["source"] not in existing]
        self.assertEqual(build(self.resources, merged)[0], self.aliases)


if __name__ == "__main__":
    unittest.main()
