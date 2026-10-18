"""验证单处修改自动同步、精确编译格式和真实语境例外的拒绝分支。"""

import unittest

from audit_source_variants import audit_generation
from prepare_variant_generation import migrate
from source_variant_generation import digest, project_subset, render_variants
from prepare_lead_followup import runtime_source


class VariantGenerationTests(unittest.TestCase):
    def fixture(self):
        raw = "We-- <i>know.</i>"
        compiled = runtime_source(raw)
        ghost = "<i>" + compiled + "</i>"
        box = "<line-height=90%>" + ghost
        rows = [{"id": str(i), "source": source, "target": target} for i, (source, target) in enumerate([
            (raw, "我们——<i>知道。</i>"), (compiled, "我们——<i>知道。</i>"),
            (ghost, "<i>我们——<i>知道。</i></i>"),
            (box, "<line-height=90%><i>我们——<i>知道。</i></i>"),
            (box + "\n", "<line-height=90%><i>我们——<i>知道。</i></i>\n")])]
        edges = [
            {"kind": "resource", "base": raw, "variant": compiled, "prefix": "", "suffix": "", "origins": ["实际资源"]},
            {"kind": "dialogue", "base": raw, "resource_source": raw, "actor": "ghost",
             "variant": ghost, "prefix": "<i>", "suffix": "</i>", "origins": ["实际幽灵对白"]}]
        for base, variant, prefix, suffix in ((ghost, box, "<line-height=90%>", ""), (box, box + "\n", "", "\n")):
            edges.append({"kind": "explicit", "base": base, "variant": variant,
                          "prefix": prefix, "suffix": suffix, "base_sha256": digest(base),
                          "variant_sha256": digest(variant), "origins": ["准确运行别名"]})
        canonical, manifest, _ = migrate(rows, edges, [], {ghost})
        return rows, canonical, manifest

    def test_one_chinese_edit_updates_all_formats_and_preserves_inner_italic(self):
        rows, canonical, manifest = self.fixture()
        canonical[0]["target"] = "我们——<i>明白了。</i>"
        targets = {row["source"]: row["target"] for row in render_variants(rows, canonical, manifest)}
        self.assertEqual(len(canonical), 1)
        self.assertEqual(targets["We-- <i>know.</i>"], "我们——<i>明白了。</i>")
        self.assertEqual(targets["<i>We—<i>know.</i></i>"], "<i>我们——<i>明白了。</i></i>")
        self.assertEqual(list(targets.values())[-1], "<line-height=90%><i>我们——<i>明白了。</i></i>\n")

    def test_single_sided_legacy_edit_is_rejected(self):
        rows, canonical, manifest = self.fixture()
        rows[0]["target"] = "我们——<i>改了一端。</i>"
        with self.assertRaisesRegex(ValueError, "单边变化"):
            render_variants(rows, canonical, manifest)

    def test_partial_historical_review_uses_same_canonical_contract(self):
        rows, canonical, manifest = self.fixture()
        self.assertEqual(project_subset(rows[:1], canonical, manifest), render_variants(rows, canonical, manifest)[:1])

    def test_bad_hash_missing_canonical_duplicate_source_or_binding_rejected(self):
        for case in ("hash", "id", "missing", "duplicate_source", "duplicate_binding", "version", "origins"):
            rows, canonical, manifest = self.fixture()
            if case == "hash": manifest["bindings"][0]["source_sha256"] = "错误"
            elif case == "id": rows[0]["id"] = "覆盖记录ID不等于词条ID"
            elif case == "missing": canonical = []
            elif case == "duplicate_source": rows.append(rows[0])
            elif case == "duplicate_binding": manifest["bindings"].append(manifest["bindings"][0])
            elif case == "version": manifest["schema_version"] = 2
            else: canonical[0]["origins"] = []
            with self.subTest(case=case), self.assertRaises(ValueError):
                render_variants(rows, canonical, manifest)

    def test_mismatched_rules_and_damaged_emphasis_rejected(self):
        rows, canonical, manifest = self.fixture()
        manifest["relationships"][1]["actor"] = "ophelia"
        with self.assertRaises(ValueError): render_variants(rows, canonical, manifest)
        rows, canonical, manifest = self.fixture()
        canonical[0]["target"] = "我们明白了。"
        with self.assertRaisesRegex(ValueError, "损坏"):
            render_variants(rows, canonical, manifest)

    def test_order_of_actual_dash_compiler_is_not_generic_normalization(self):
        self.assertEqual(runtime_source("A---B"), "A—-B")
        self.assertEqual(runtime_source("A - B -- C --- D"), "A—B—C—D")
        self.assertEqual(runtime_source("A  B"), "A  B")

    def test_two_actual_runtime_values_cannot_be_silently_merged(self):
        rows, _, manifest = self.fixture()
        rows[0]["target"] = "我们——<i>另有含义。</i>"
        with self.assertRaisesRegex(ValueError, "实际运行译文"):
            migrate(rows, manifest["relationships"], [], {row["source"] for row in rows})

    def test_context_exception_keeps_separate_chinese_and_rejects_forced_merge(self):
        rows = [{"id": "a", "source": "I do.", "target": "是的。"},
                {"id": "b", "source": "<i>I do.</i>", "target": "<i>是的，我也一样。</i>"}]
        edge = {"kind": "dialogue", "actor": "ghost", "base": "I do.", "resource_source": "I do.",
                "variant": "<i>I do.</i>", "prefix": "<i>", "suffix": "</i>",
                "origins": ["真实共享对白"], "reason": "裸源用于其他人物的不同语境"}
        canonical, manifest, result = migrate(rows, [], [edge], {row["source"] for row in rows})
        self.assertEqual([row["target"] for row in result], [row["target"] for row in rows])
        manifest["bindings"][1]["canonical_id"] = manifest["bindings"][0]["canonical_id"]
        with self.assertRaises(ValueError): render_variants(rows, canonical, manifest)

    def test_new_real_pair_must_be_registered(self):
        _, _, manifest = self.fixture()
        edge = manifest["relationships"][1]
        pairs = [{"actor": "ghost", "source": edge["resource_source"], "runtime_source": edge["variant"]}]
        self.assertFalse(audit_generation(pairs, manifest)["unmanaged_pairs"])
        pairs[0]["source"] = "New-- line"
        self.assertEqual(len(audit_generation(pairs, manifest)["unmanaged_pairs"]), 1)

    def test_identical_non_ghost_format_is_shared_across_actors(self):
        manifest = {"relationships": [{"kind": "dialogue", "actor": "ophelia",
                     "resource_source": "I--", "variant": "I—"}], "context_exceptions": []}
        pairs = [{"actor": actor, "source": "I--", "runtime_source": "I—"}
                 for actor in ("ophelia", "hamlet", "gertrude")]
        result = audit_generation(pairs, manifest)
        self.assertEqual(result, {"pairs_covered": 3, "unmanaged_pairs": []})


if __name__ == "__main__":
    unittest.main()
