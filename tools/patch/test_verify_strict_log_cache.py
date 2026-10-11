"""混合日志缓存的判定器门禁回归。"""

import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("strict_cache", Path(__file__).with_name("verify-strict-log-cache.py"))
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class CacheVerificationTests(unittest.TestCase):
    def setUp(self):
        self.cases = b"one\tYQ==\tYg==\n"
        self.report = "SOURCE_SHA256\t" + hashlib.sha256(self.cases).hexdigest() + "\nCASE\tone\tTrue\tTrue\tTrue\tTrue\tTrue\nUNKNOWN_REJECTED\tTrue\nSUMMARY\tTrue\t1\n"

    def test_complete(self):
        self.assertTrue(verify.analyze(self.report, self.cases)["passed"])

    def test_partial_repair_or_f8_failure_rejected(self):
        for column in range(2, 7):
            rows = self.report.splitlines()
            fields = rows[1].split("\t")
            fields[column] = "False"
            rows[1] = "\t".join(fields)
            self.assertFalse(verify.analyze("\n".join(rows), self.cases)["passed"])

    def test_duplicate_or_wrong_fixture_rejected(self):
        self.assertFalse(verify.analyze(self.report + "CASE\tone\tTrue\tTrue\tTrue\tTrue\tTrue\n", self.cases)["passed"])
        self.assertFalse(verify.analyze(self.report, self.cases + b"two\tYQ==\tYg==\n")["passed"])

    def test_unknown_or_missing_completion_rejected(self):
        self.assertFalse(verify.analyze(self.report.replace("UNKNOWN_REJECTED\tTrue", "UNKNOWN_REJECTED\tFalse"), self.cases)["passed"])
        self.assertFalse(verify.analyze(self.report.split("SUMMARY")[0], self.cases)["passed"])
