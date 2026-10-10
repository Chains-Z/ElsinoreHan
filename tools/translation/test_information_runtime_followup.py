"""检查所有真实信息字段的运行变体覆盖和译文复用治理。"""
import json
import unittest

from prepare_information_runtime_followup import ROOT, RESOURCE, build, digest, source_rows


class InformationRuntimeFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.assets = source_rows(RESOURCE.read_bytes())
        cls.translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8-sig"))

    def test_all_three_real_assets_and_long_short_fields_are_covered(self):
        self.assertEqual(len(self.assets), 3)
        self.assertEqual(sum(a["information_count"] for a in self.assets), 55)
        self.assertEqual(len(self.rows), 110)
        changed = [r for r in self.rows if r["source"] != r["runtime_source"]]
        self.assertEqual(len(changed), 4)
        self.assertEqual({r["origin"]["record_id"] for r in changed}, {"SimonaLives", "BernardoBoyPlayer"})

    def test_aliases_reuse_governed_targets_and_all_fields_have_cases(self):
        aliases, cases = build(self.rows, self.translations)
        self.assertEqual(len(aliases), 2)
        self.assertEqual(len(cases), 110)
        by_source = {r["source"]: r for r in self.translations}
        for alias in aliases:
            self.assertEqual(alias["target"], by_source[alias["existing_source"]]["target"])
            self.assertEqual(alias["source_sha256"], digest(alias["source"]))
            self.assertEqual(alias["existing_target_sha256"], digest(alias["target"]))
            self.assertEqual({o["field"] for o in alias["origins"] if isinstance(o, dict)}, {"long", "short"})
        for case in cases:
            self.assertEqual(case["target"], by_source[case["source"]]["target"])

    def test_conflicting_runtime_target_is_rejected(self):
        row = next(r for r in self.rows if r["source"] != r["runtime_source"])
        source = row["runtime_source"]
        changed = [{**r, "target": "冲突译文"} if r["source"] == source else r for r in self.translations]
        with self.assertRaisesRegex(ValueError, "冲突"):
            build(self.rows, changed)


if __name__ == "__main__":
    unittest.main()
