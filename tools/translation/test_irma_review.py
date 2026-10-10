"""检查昵称校订的全表覆盖、称呼边界及治理保护。"""

import hashlib
import json
import re
import unittest

from export_sol_full import ROOT, apply_supplemental


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class IrmaReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read("translation/sol-full-2026-10-09/translations.json")
        cls.by_id = {row["id"]: row for row in cls.rows}

    def test_nickname_is_consistent_without_replacing_full_name(self):
        rows = [r for r in self.rows if re.search(r"\bGerta\b", r["source"], re.I)]
        self.assertEqual(len(rows), 59)
        for row in rows:
            with self.subTest(id=row["id"]):
                self.assertIn("格尔塔", row["target"])
                self.assertNotRegex(row["target"], r"乔塔|乔蒂|乔特(?!鲁德)|格尔塔鲁德")
                if "Gertrude" in row["source"]:
                    self.assertIn("乔特鲁德", row["target"])
                if re.search(r"G-[gG]erta", row["source"]):
                    self.assertIn("格、格尔塔", row["target"])
                # 昵称替换不能改变原有富文本标记及标记的顺序。
                self.assertEqual(re.findall(r"<[^>]*>", row["source"]),
                                 re.findall(r"<[^>]*>", row["target"]))

    def test_biene_vocatives_and_aye_answer(self):
        rows = [r for r in self.rows if re.search(r"\bBiene\b", r["source"])]
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertIn("姑娘", row["target"])
            self.assertNotIn("比内", row["target"])
        self.assertTrue(self.by_id["p05725-8ba1ea3362fc"]["target"].startswith("相信，王后。"))

    def test_senior_guard_preserves_requested_wording(self):
        target = self.by_id["p15096-2e2aaa47cce5"]["target"]
        self.assertIn("资历最老", target)
        self.assertNotIn("嘛", target)
        self.assertNotIn("资历最深", target)
        self.assertNotIn("我", target)

    def test_every_review_correction_rejects_stale_previous_target(self):
        corrections = read("translation/supplemental/irma-corrections.json")
        self.assertEqual(len(corrections), 38)
        for row in corrections:
            with self.subTest(id=row["id"]):
                self.assertEqual(hashlib.sha256(row["source"].encode()).hexdigest(), row["source_sha256"])
                base = [{"id": "base", "source": row["source"], "target": row["previous_target"]}]
                self.assertEqual(apply_supplemental(base, [row])[0]["target"], row["target"])
                with self.assertRaises(ValueError):
                    apply_supplemental(base, [{**row, "previous_target": "不匹配的旧译文"}])


if __name__ == "__main__":
    unittest.main()
