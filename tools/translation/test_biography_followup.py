"""核验人物简介来源、别名治理和有限保序规则，不冒充游戏界面验收。"""

import base64
import copy
import itertools
import json
from pathlib import Path
import re
import unittest

from export_sol_full import apply_supplemental
from prepare_biography_followup import ROOT, build, digest, extract_resources, resolve_original


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def python_pattern(pattern):
    """仅把此组规则使用的命名捕获和严格尾锚转为Python；真实消费另由.NET验证。"""
    return re.compile(re.sub(r"\(\?<([a-z_]+)>", r"(?P<\1>", pattern).replace(r"\z$", r"\Z").replace(r"\z", r"\Z"))


class BiographyFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.translations = [row for row in read("translation/sol-full-2026-10-09/translations.json")
                            if not row["id"].startswith("ui-bio-runtime-")]
        cls.resources, cls.resources_sha = extract_resources(
            Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/resources.assets"))
        cls.aliases, cls.rules, cls.cases, cls.groups, cls.ordered_count = build(cls.resources, cls.translations)
        cls.patterns = {row["id"].removeprefix("ui-rule-biography-paragraphs-"): python_pattern(row["pattern"])
                        for row in cls.rules}

    def test_complete_real_source_scope(self):
        self.assertEqual(self.resources_sha, "6d0ae1f735d95db40b836cedfc25e92143aa3727fee7bcd71e0cb319320961fd")
        self.assertEqual(len(self.resources), 3)
        self.assertEqual(len(self.groups), 18)
        self.assertEqual(sum(len(actor["lines"]) for resource in self.resources for actor in resource["actors"]), 104)
        self.assertEqual(self.ordered_count, 345)
        self.assertEqual(len(self.cases), 738)
        self.assertEqual(len(self.rules), 16)

    def test_all_ordered_multi_line_subsets_match_with_line_height(self):
        count = 0
        for actor, group in self.groups.items():
            for version in group["versions"]:
                for size in range(2, len(version["lines"]) + 1):
                    for parts in itertools.combinations(version["lines"], size):
                        for prefix in ("", "<line-height=90%>"):
                            source = prefix + "\n\n".join(row["source"] for row in parts)
                            with self.subTest(actor=actor, parts=[row["line_id"] for row in parts], prefix=prefix):
                                match = self.patterns[actor].fullmatch(source)
                                self.assertIsNotNone(match)
                                self.assertEqual(match["first"], parts[0]["source"])
                                self.assertEqual(match["rest"], "\n\n".join(row["source"] for row in parts[1:]))
                                count += 1
        self.assertEqual(count, 482)

    def test_unknown_front_middle_back_rejected(self):
        cases = [row for row in self.cases if row["target"] is None]
        self.assertEqual(len(cases), 48)
        for case in cases:
            for actor, pattern in self.patterns.items():
                with self.subTest(case=case["id"], actor=actor):
                    self.assertIsNone(pattern.fullmatch(case["source"]))

    def test_reverse_duplicate_and_trailing_lf_rejected(self):
        for actor, group in self.groups.items():
            if actor not in self.patterns:
                continue
            version = max(group["versions"], key=lambda item: len(item["lines"]))
            sources = [row["source"] for row in version["lines"]]
            for source in ("\n\n".join(reversed(sources)), "\n\n".join([sources[0], sources[0]]),
                           "\n\n".join(sources) + "\n"):
                with self.subTest(actor=actor, source=source[:80]):
                    self.assertIsNone(self.patterns[actor].fullmatch(source))

    def test_six_aliases_reuse_governed_targets_exactly(self):
        self.assertEqual(len(self.aliases), 6)
        self.assertEqual({row["existing_id"].split("-")[0] for row in self.aliases},
                         {"p00549", "p00047", "p00588", "p10552", "p10553", "p10554"})
        merged = apply_supplemental(self.translations, self.aliases)
        by_source = {row["source"]: row for row in merged}
        for alias in self.aliases:
            with self.subTest(alias=alias["id"]):
                self.assertEqual(by_source[alias["source"]]["target"], alias["target"])
                changed = copy.deepcopy(alias)
                changed["existing_target_sha256"] = digest("过期目标")
                with self.assertRaises(ValueError):
                    apply_supplemental(self.translations, [changed])

    def test_whitespace_lookup_must_be_unique(self):
        raw = "English\n\n text"
        entries = [{"id": "one", "source": "English text", "target": "正文"}]
        self.assertEqual(resolve_original(raw, raw, entries)["id"], "one")
        with self.assertRaises(ValueError):
            resolve_original(raw, raw, entries + [{"id": "two", "source": " English text ", "target": "另一正文"}])

    def test_source_hash_tamper_is_rejected(self):
        resources = copy.deepcopy(self.resources)
        resources[0]["actors"][0]["lines"][0]["source"] += " tamper"
        with self.assertRaises(ValueError):
            build(resources, self.translations)

    def test_screenshot_runtime_case_is_exact_current_hamlet_pair(self):
        path = ROOT / "runtime/build/biography-followup/runtime-cases.tsv"
        fields = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(fields), 19)
        row = next(row for row in fields if row[0] == "bio-runtime-screenshot-hamlet")
        self.assertEqual(row[3], "hamlet")
        source = base64.b64decode(row[1]).decode("utf-8")
        target = base64.b64decode(row[2]).decode("utf-8")
        self.assertTrue(source.startswith("Hamlet recently lost his father"))
        self.assertIn("\n\nHamlet and I were together for two years, in secret.", source)
        self.assertTrue(target.startswith("<line-height=90%>"))


if __name__ == "__main__":
    unittest.main()
