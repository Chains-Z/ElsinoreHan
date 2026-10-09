"""混合日志来源、完整类型/简称矩阵、尾LF治理及称号区别回归。"""

import copy
import unittest

from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import ROOT, read, digest
from prepare_mixed_log_followup import OUT, FULL, BUILD


class MixedLogFollowupTests(unittest.TestCase):
    def test_real_four_types_and_all_shortnames_are_present(self):
        manifest = read(BUILD / "manifest.json")
        self.assertEqual(set(manifest["types"]), {"Dialogue", "LogicChange", "Stage", "Alert"})
        self.assertEqual(manifest["character_ids"], 55)
        audit = read(ROOT / "analysis/ui-audit/dialogue-log-source-audit.json")
        self.assertEqual(set(manifest["shortnames"]), set(audit["short_names"].values()))
        self.assertEqual(len(manifest["shortnames"]), 45)

    def test_all_current_dialogues_and_notification_pairs_are_covered(self):
        manifest = read(BUILD / "manifest.json")
        self.assertEqual(manifest["categories"]["all_dialogues"], 11554 * 2)
        self.assertEqual(manifest["categories"]["all_shortnames"], manifest["notification_variants"] * 45 * 3)
        self.assertEqual(manifest["pair_case_count"], manifest["notification_variants"] ** 2 + 55 ** 2)
        self.assertEqual(manifest["categories"]["negative"], 8)

    def test_screenshot_contains_real_bold_future_and_two_bernardo_lines(self):
        row = next(r for r in read(OUT / "mixed-log-representative-tests.json") if r["category"] == "screenshot")
        self.assertTrue(row["source"].startswith("<b>Ophelia</b> learns about a future event in which "))
        self.assertIn("<b>Bernardo:</b>", row["source"])
        self.assertIn("I turn to the court with a more pressing matter.\nMy lord,", row["source"])
        self.assertIn("<b>贝尔纳多:</b>", row["target"])
        self.assertIn("<b>时间线</b>", row["target"])

    def test_different_actor_ids_with_same_shortname_keep_two_labels(self):
        audit = read(ROOT / "analysis/ui-audit/dialogue-log-source-audit.json")
        actors = sorted(audit["short_names"])
        rows = {r["id"]: r for r in read(OUT / "mixed-log-pair-tests.json")}
        def pair(first, second):
            index = actors.index(first) * len(actors) + actors.index(second)
            return rows["mixed-all-speaker-pair-" + str(index)]
        self.assertEqual(audit["short_names"]["brigand"], audit["short_names"]["brigand2"])
        self.assertEqual(pair("brigand", "brigand")["source"].count("<b>Brigand:</b>"), 1)
        self.assertEqual(pair("brigand", "brigand2")["source"].count("<b>Brigand:</b>"), 2)

    def test_only_boundary_groups_are_ignored_and_sources_are_recorded(self):
        rules = read(OUT / "mixed-log-rules.json")
        self.assertEqual(len(rules), 6)
        for row in rules:
            self.assertTrue(row["origins"])
            self.assertTrue(row["pattern"].startswith("^"))
            self.assertTrue(row["pattern"].endswith(r"\z$"))
        self.assertEqual(next(r for r in rules if r["id"] == "ui-rule-mixed-log-notification-boundary")["replacement"],
                         "${first}${newline_i}${rest}")

    def test_terminal_aliases_do_not_change_translation_body(self):
        targets = {r["source"]: r for r in read(FULL / "translations.json")}
        for row in read(OUT / "mixed-log-translations.json"):
            base = targets[row["base_source"]]
            self.assertEqual(row["source"], base["source"] + "\n")
            self.assertEqual(row["target"], base["target"] + "\n")
            self.assertEqual(row["base_target_sha256"], digest(base["target"]))
            self.assertEqual(row["source_sha256"], digest(row["source"]))
            base_rows = [base]
            self.assertEqual(apply_supplemental(base_rows, [row])[-1]["target"], row["target"])
            corrupt = copy.deepcopy(row)
            corrupt["target"] = "未经允许的新正文。\n"
            with self.assertRaises(ValueError):
                apply_supplemental(base_rows, [corrupt])

    def test_shared_title_keeps_captain_and_member_different(self):
        targets = {r["source"]: r["target"] for r in read(FULL / "translations.json")}
        self.assertEqual(targets["Lord of Denmark, Knight-Guard Captain"], "丹麦贵族，骑士卫队队长")
        self.assertEqual(targets["Knight-Guard of Elsinore"], "埃尔西诺骑士卫队成员")


if __name__ == "__main__":
    unittest.main()
