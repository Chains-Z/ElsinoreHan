"""使用最小夹具检查重放判定器的拒绝分支；不冒称真实游戏验收。"""

import base64
import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("biography_verifier", Path(__file__).with_name("verify-biography-replay.py"))
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def enc(value):
    return base64.b64encode(value.encode()).decode()


class BiographyReplayTests(unittest.TestCase):
    def setUp(self):
        source, target = "First paragraph.\n\nSecond paragraph.", "<line-height=90%>第一段。\n\n第二段。"
        wrapped = "<line-height=90%>" + source
        self.cases = f"hamlet-all\t{enc(source)}\t{enc(target)}\thamlet\nmissing-all\t{enc('Missing.')}\t{enc('<line-height=90%>不可见。')}\tghost\n".encode()
        self.rows = [
            ["SCHEMA", "1"], ["SCOPE", "real_resource_component_replay"],
            ["INPUT_SHA256", hashlib.sha256(self.cases).hexdigest()],
            ["EXPECTED", "hamlet-all", "hamlet", enc(source), enc(target)],
            ["EXPECTED", "missing-all", "ghost", enc("Missing."), enc("<line-height=90%>不可见。")],
            ["CONTROL", "hamlet", "123", "True", "True", "True"],
            ["SOURCE", "hamlet-all", "hamlet", "123", enc(wrapped)],
        ]
        for mode in ("translated", "original", "restored"):
            self.rows.append(["TEXT", "hamlet-all", mode, "123", "True", enc(wrapped if mode == "original" else target),
                              enc(wrapped), "False" if mode == "original" else "True"])
        self.rows.extend([
            ["API", "hamlet-all", "True", enc(target), enc(target)],
            ["RESTORE", "hamlet", "123", enc("initial"), enc("initial"), enc("原文显示"), enc("原文显示"), "True", "True", "True"],
            ["ACTOR_STATUS", "hamlet", "COLLECTED"],
            ["UNAVAILABLE", "missing-all", "ghost", "no_frozen_portrait"], ["STATUS", "COLLECTED"],
        ])
        self.journal = "CONTROL\tcharacter:hamlet\tcharacter.profile.body\t123\tpath\tTrue\n"

    def result(self):
        return verifier.analyze("\n".join("\t".join(row) for row in self.rows), self.cases, self.journal, minimum_actors=1)

    def row(self, name):
        return next(row for row in self.rows if row[0] == name)

    def test_complete_resource_component_roundtrip_passes(self):
        self.assertTrue(self.result()["passed"])

    def test_missing_f8_leg_fails(self):
        self.rows.remove(next(row for row in self.rows if row[:3] == ["TEXT", "hamlet-all", "restored"]))
        self.assertFalse(self.result()["passed"])

    def test_english_showing_in_chinese_mode_fails(self):
        self.row("TEXT")[5] = enc("<line-height=90%>First paragraph.")
        self.assertFalse(self.result()["passed"])

    def test_body_identity_change_fails(self):
        self.row("TEXT")[3] = "124"
        self.assertFalse(self.result()["passed"])

    def test_fixture_digest_mismatch_fails(self):
        self.row("INPUT_SHA256")[1] = "0" * 64
        self.assertFalse(self.result()["passed"])

    def test_cache_absence_fails_even_when_display_correct(self):
        self.row("API")[2] = "False"
        self.assertFalse(self.result()["passed"])

    def test_builder_mutation_fails(self):
        self.row("TEXT")[6] = enc("changed")
        self.assertFalse(self.result()["passed"])

    def test_restore_display_mismatch_fails(self):
        self.row("RESTORE")[6] = enc("变化了")
        self.assertFalse(self.result()["passed"])

    def test_missing_explicit_unavailable_scope_fails(self):
        self.rows.remove(self.row("UNAVAILABLE"))
        self.assertFalse(self.result()["passed"])

    def test_duplicate_available_actor_fails(self):
        self.rows.append(self.row("CONTROL")[:])
        self.assertFalse(self.result()["passed"])

    def test_wrong_real_journal_control_fails(self):
        self.journal = self.journal.replace("123", "999")
        self.assertFalse(self.result()["passed"])

    def test_unknown_row_rejected(self):
        self.rows.append(["FAKE", "True"])
        self.assertFalse(self.result()["passed"])


if __name__ == "__main__":
    unittest.main()
