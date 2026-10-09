"""仅测试证据校验器契约；合成TSV测试夹具不作为运行时或剧情验收。"""
import base64
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("verify-timeline-followup.py")
SPEC = importlib.util.spec_from_file_location("timeline_followup_verifier", MODULE)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def b64(value):
    return base64.b64encode(value.encode()).decode()


def fixture():
    """用冻结完整源构造最小校验器夹具，标签明确表示局部契约测试。"""
    _, tests, event_ids = verifier.load_contracts()
    frozen = tests[verifier.REPLAY_KEYS["replay-hamlet-sleep"]]
    source, target = frozen["source"], frozen["target"]
    description = "Hamlet's ravings interrupt my sleep."
    rows = [["SCHEMA", "1"], ["METHOD", "合成证据校验器单元测试夹具"], ["START_LOOP", "1"]]
    rows.append(["INITIAL_DETAIL", b64("test-key"), b64(source), verifier.sha(source), "True"])
    rows.append(["OWNER", "INITIAL", "initial", "translated", "True", "True", "True", "True", "True",
                 "False", "True", "True", "True", "True"])
    secondary = "<line-height=90%>Including Hamlet." + verifier.TAIL
    rows.append(["REAL", "real-empty-one", "1", b64("test-key"), next(iter(event_ids[description])), "True", "1", "0",
                 b64("Ophelia's Chambers"), b64(description), b64("Hamlet"), b64("hamlet"), b64(source), verifier.sha(source),
                 b64(secondary), "True", "True", "button.OnClick", "currentItems", "TimelineItem.Details(lastUsedGameState)"])

    def states(kind, key, source, target):
        for mode, displayed in [("translated", target), ("original", source), ("restored", target)]:
            rows.append(["OWNER", kind, key, mode, "True", "True", "True", "True", "True",
                         "False", "True", "True", "True", "True"])
            rows.append(["STATE", kind, key, mode, "99", b64(source), verifier.sha(source), b64(displayed), b64(source),
                         "True", "1802", "True" if kind == "REAL" else "False"])

    states("REAL", "real-empty-one", source, target)
    descriptions = [description, "Polonius questions Hamlet.", "Horatio and Gertrude have a heart to heart.",
                    "Quince puts on the play that Hamlet designed.", "Hamlet presses his Mother on Claudius's actions."]
    names = ["Hamlet", "Hamlet\nPolonius", "Queen Gertrude\nHoratio", "King Claudius\nQueen Gertrude\nHamlet\nHoratio\nQuince", ""]
    rooms = ["Ophelia's Chambers", "The Royal Gallery", "The Grounds", "The Great Hall", "Gertrude's Chambers"]
    clocks = ["Thursday, 06:02", "Thursday, 11:43", "Saturday, 08:02", "Friday, 17:15", "Saturday, 00:30"]
    for index, (key, test_key) in enumerate(verifier.REPLAY_KEYS.items()):
        row = tests[test_key]
        desc = descriptions[index]
        rows.append(["REPLAY", key, next(iter(event_ids[desc])), b64(desc), verifier.sha(desc), b64(rooms[index]), b64(clocks[index]),
                     b64(names[index]), b64(row["source"]), verifier.sha(row["source"]), "real-resource-formatter-component",
                     "not-acquired-story", b64(names[index]), "ElsinoreEvent.Participants+Observers/UiStrings.FormatCharacterName"])
        states("REPLAY", key, row["source"], row["target"])
    for role, status in [("empty-one", "AVAILABLE"), ("empty-many", "UNAVAILABLE"), ("queen-room", "UNAVAILABLE")]:
        rows.append(["COVERAGE", role, status, b64("合成夹具中的覆盖说明")])
    for description in descriptions:
        rows.append(["STORY_COVERAGE", b64(description), "UNAVAILABLE", "单元测试夹具不表示真实剧情覆盖"])
    rows.append(["RESTORE", "1", b64("test-key"), b64(source), b64(source), "True", "True", "original-item.button.OnClick"])
    rows.append(["STATUS", "COMPLETE", "1", "7.5"])
    return rows


class TimelineVerifierTests(unittest.TestCase):
    def test_complete_contract(self):
        proof = verifier.verify_rows(fixture())
        self.assertEqual(proof["real_empty_changes_details"], 1)
        self.assertEqual(proof["real_resource_formatter_replays"], 5)

    def assert_rejected(self, mutate, message):
        rows = fixture()
        mutate(rows)
        with self.assertRaisesRegex(ValueError, message):
            verifier.verify_rows(rows)

    def test_replay_cannot_replace_real_button(self):
        def mutate(rows):
            rows[:] = [row for row in rows if row[0] != "REAL" and not (row[0] == "STATE" and row[1] == "REAL")]
            rows[-1][2] = "0"
        self.assert_rejected(mutate, "组件重放不能代替")

    def test_missing_original_state(self):
        self.assert_rejected(lambda rows: rows.pop(next(index for index, row in enumerate(rows)
                             if row[0] == "STATE" and row[3] == "original")), "三态未完整")

    def test_english_body_rejected(self):
        def mutate(rows):
            for row in rows:
                if row[:3] == ["STATE", "REAL", "real-empty-one"] and row[3] != "original": row[7] = b64("Including Hamlet.")
        self.assert_rejected(mutate, "英文漏译")

    def test_original_source_truncated(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "STATE" and row[3] == "original").__setitem__(7, b64("Hamlet")), "完整真实原文")

    def test_current_owner_required(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "STATE").__setitem__(9, "False"), "UI归属")

    def test_builder_must_stay_english(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "STATE").__setitem__(8, b64("被改写的原文")), "builder源变更")

    def test_same_control_and_clock(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "STATE").__setitem__(4, "100"), "控件或真实暂停时钟")

    def test_replay_source_hash(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "REPLAY").__setitem__(9, "0" * 64), "哈希不符")

    def test_wrong_real_event_source(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "REAL").__setitem__(4, "FAKE_EVENT"), "冻结资源来源")

    def test_no_fake_loop_navigation(self):
        self.assert_rejected(lambda rows: rows.insert(3, ["LOOP_NAV", "ShowDifferentLoop", "1", "0", "True"]), "真实左右按钮")

    def test_no_unfinished_navigation(self):
        self.assert_rejected(lambda rows: rows.insert(3, ["LOOP_NAV", "PreviousLoopButton.OnClick", "1", "2", "False"]), "请求未完成")

    def test_replay_not_acquired_story(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "REPLAY").__setitem__(11, "acquired-story"), "错误记为真实剧情")

    def test_available_requires_real_sample(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[:2] == ["COVERAGE", "empty-many"]).__setitem__(2, "AVAILABLE"), "重放或无关事件冒充")

    def test_unknown_people_rejected(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "REAL").__setitem__(10, b64("UNKNOWN_PERSON")), "完整名单源不符")

    def test_story_absence_must_be_reported(self):
        self.assert_rejected(lambda rows: rows.pop(next(index for index, row in enumerate(rows) if row[0] == "STORY_COVERAGE")), "独立未覆盖说明")

    def test_original_loop_must_restore(self):
        self.assert_rejected(lambda rows: rows.insert(3, ["LOOP_NAV", "PreviousLoopButton.OnClick", "1", "2", "True"]), "未恢复最初loop")

    def test_real_history_index_direction_and_return(self):
        rows = fixture()
        rows[3:3] = [["LOOP_NAV", "PreviousLoopButton.OnClick", "1", "2", "True"],
                     ["LOOP_NAV", "NextLoopButton.OnClick", "2", "1", "True"]]
        self.assertTrue(verifier.verify_rows(rows)["f8_source_complete"])

    def test_original_detail_must_restore_by_button(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "RESTORE").__setitem__(7, "text.SetText"), "真实原按钮")

    def test_original_detail_must_restore_completely(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "RESTORE").__setitem__(4, b64("截断原文")), "没有恢复")

    def test_replay_room_origin_must_match(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "REPLAY").__setitem__(5, b64("UnknownRoom")), "时钟/房间参数")

    def test_replay_participant_origin_must_match(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "REPLAY").__setitem__(7, b64("Polonius")), "完整名单源不一致")

    def test_other_dialog_cannot_own_timeline_text(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "OWNER").__setitem__(10, "False"), "自己的激活详情弹窗")

    def test_own_dialog_requires_current_timeline_canvas(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "OWNER").__setitem__(8, "False"), "自己的激活详情弹窗")

    def test_own_dialog_requires_body_inside_popup(self):
        self.assert_rejected(lambda rows: next(row for row in rows if row[0] == "OWNER").__setitem__(12, "False"), "自己的激活详情弹窗")

    def test_future_item_skip_does_not_replace_real_changes(self):
        rows = fixture()
        description = "Polonius questions Hamlet."
        rows.insert(4, ["SKIP", "1", b64("future-key"), "SC_SPINE_HamletPolonius", "False", "True", b64(description),
                        verifier.sha(description), "not-attended-or-future", "", "Details-not-called", b64("future-scene")])
        proof = verifier.verify_rows(rows)
        self.assertEqual(proof["real_empty_changes_details"], 1)
        self.assertEqual(proof["skipped_items"][0]["reason"], "not-attended-or-future")

    def test_missing_scene_changes_skip_is_reported(self):
        rows = fixture()
        description = "Polonius questions Hamlet."
        rows.insert(4, ["SKIP", "1", b64("past-key"), "SC_SPINE_HamletPolonius", "True", "False", b64(description),
                        verifier.sha(description), "details-missing-scene", b64("KeyNotFoundException: missing real scene"),
                        "TimelineItem.Details(lastUsedGameState)", b64("missing-real-scene")])
        proof = verifier.verify_rows(rows)
        self.assertEqual(proof["real_empty_changes_details"], 1)
        self.assertEqual(proof["skipped_items"][0]["scene_ids"], ["missing-real-scene"])

    def test_unattended_event_cannot_claim_zero_changes(self):
        def mutate(rows):
            row = next(row for row in rows if row[0] == "REAL")
            row[5] = "False"
        self.assert_rejected(mutate, "不得调用Details或虚构零Changes")

    def test_initial_matcher_missing_scene_is_not_fake_success(self):
        rows = fixture()
        description = "Polonius questions Hamlet."
        rows.insert(4, ["SKIP", "1", b64("past-key"), "SC_SPINE_HamletPolonius", "True", "False", b64(description),
                        verifier.sha(description), "details-missing-scene", b64("KeyNotFoundException: missing real scene"),
                        "createEventContent->TimelineItem.Details(lastUsedGameState)", b64("missing-real-scene")])
        proof = verifier.verify_rows(rows)
        self.assertEqual(proof["real_empty_changes_details"], 1)


if __name__ == "__main__":
    unittest.main()
