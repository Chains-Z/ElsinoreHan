"""核验多人通知边界的来源语法与幂等修订；真实递归消费者另行执行。"""

import copy
import re
import unittest

from prepare_notification_list_followup import OUT, read, repair_rows, format_people, people_pattern


class NotificationListFollowupTests(unittest.TestCase):
    def test_true_three_person_format(self):
        source, target = format_people(["Queen Gertrude", "Polonius", "King Claudius"],
                                      {"Queen Gertrude": "乔特鲁德王后", "Polonius": "波洛涅斯", "King Claudius": "克劳狄斯国王"})
        self.assertEqual(source, '<b>Queen Gertrude</b>, <b>Polonius</b>, and <b>King Claudius</b>')
        self.assertEqual(target, '<b>乔特鲁德王后</b>、<b>波洛涅斯</b>和<b>克劳狄斯国王</b>')

    def test_original_boundary_rejects_oxford_new_accepts(self):
        old, new = people_pattern()
        source = '<b>Queen Gertrude</b>, <b>Polonius</b>, and <b>King Claudius</b> now believe that "Fortinbras will cross Denmark".'
        self.assertIsNone(re.match(old, source))
        self.assertIsNotNone(re.match(new, source))

    def test_one_two_three_five_all_match(self):
        _, pattern = people_pattern()
        names = ["Queen Gertrude", "Polonius", "King Claudius", "Bernardo", "Hamlet"]
        targets = {n: n for n in names}
        for count in (1, 2, 3, 5):
            source, _ = format_people(names[:count], targets)
            self.assertIsNotNone(re.fullmatch(pattern, source + " "))

    def test_unknown_name_rejected(self):
        _, pattern = people_pattern()
        self.assertIsNone(re.fullmatch(pattern, '<b>UnknownActor</b>, <b>Polonius</b>, and <b>King Claudius</b> '))

    def test_repair_idempotent_and_other_rules_unchanged(self):
        original = read(OUT / "notification-ui-rules.json")
        updated = repair_rows(copy.deepcopy(original))
        self.assertEqual(updated, repair_rows(copy.deepcopy(updated)))
        changed = {"ui-rule-notification-line-boundary", "ui-rule-notification-final-newlines", "ui-rule-notification-terminal-paragraph"}
        for before, after in zip(original, updated):
            if before["id"] not in changed:
                self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
