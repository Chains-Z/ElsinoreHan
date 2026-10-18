"""验证双源检查不会吞掉强调差异，且能发现单边校订与过期运行别名。"""

import unittest

from audit_source_variants import audit_aliases, collect_pairs, compare_targets, is_reviewed, signature


class SourceVariantTests(unittest.TestCase):
    def test_remove_only_compiler_added_italic(self):
        self.assertTrue(compare_targets("ghost", "<i>原有强调</i>", "<i><i>原有强调</i></i>")["equal"])
        self.assertFalse(compare_targets("ghost", "<i>原有强调</i>", "<i>原有强调</i>")["equal"])

    def test_preserve_inner_emphasis_scope(self):
        row = compare_targets("ghost", "你<i>已经回去过了</i>", "<i>你已经<i>回去过了</i></i>")
        self.assertFalse(row["equal"])
        self.assertTrue(row["formatting_only"])

    def test_missing_ghost_outer_is_not_equal(self):
        self.assertTrue(compare_targets("ghost", "相同", "相同")["missing_runtime_outer_italic"])

    def test_no_italic_normalization_for_other_actors(self):
        self.assertFalse(compare_targets("ophelia", "回答", "<i>回答</i>")["equal"])

    def test_changed_either_target_invalidates_review(self):
        row = {"source": "raw", "runtime_source": "<i>raw</i>",
               "resource_target": "旧译", "runtime_target": "<i>另一版旧译</i>"}
        baseline = signature(row)
        self.assertTrue(is_reviewed(row, baseline))
        self.assertFalse(is_reviewed({**row, "resource_target": "新译"}, baseline))
        self.assertFalse(is_reviewed({**row, "runtime_target": "<i>新译</i>"}, baseline))

    def test_compiled_missing_cannot_use_obsolete_exclusion(self):
        dialogue = [{"actor": "ghost", "source": "real", "runtime_source": "<i>real</i>", "origins": []}]
        _, exclusions, missing = collect_pairs([], dialogue, {"<i>real</i>"})
        self.assertFalse(exclusions)
        self.assertEqual(len(missing), 1)
        _, exclusions, missing = collect_pairs([], dialogue, set())
        self.assertEqual(len(exclusions), 1)
        self.assertFalse(missing)

    def test_updated_base_rejects_stale_box_alias(self):
        rows = [{"source": "base", "target": "新译"},
                {"source": "<line-height=90%>base", "target": "<line-height=90%>旧译"}]
        entries = [{"source": "<line-height=90%>base", "existing_source": "base",
                    "runtime_prefix": "<line-height=90%>"}]
        checked, mismatches = audit_aliases(rows, entries)
        self.assertEqual(checked, 1)
        self.assertEqual(len(mismatches), 1)


if __name__ == "__main__":
    unittest.main()
