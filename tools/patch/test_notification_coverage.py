"""当前消费者证据和旧阶段哈希的门禁单元测试，不冒称消费者实际执行。"""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("journal_coverage", Path(__file__).with_name("verify-journal-probe.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ROOT = Path(__file__).resolve().parents[2]
FILES = ["translation/supplemental/notification-ui-tests.json", "translation/supplemental/notification-ui-rules.json"]


class NotificationCoverageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.tests = json.loads((ROOT / FILES[0]).read_text(encoding="utf-8"))
        for relative in FILES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.evidence = {"notification_suite": {"actual_recursive_xunity_consumer_passed": True, "count": len(self.tests)},
                         "artifact_sha256": {relative: hashlib.sha256((self.root / relative).read_bytes()).hexdigest() for relative in FILES}}

    def test_current_matching_evidence_passes(self):
        self.assertTrue(module.notification_coverage_valid(self.tests, self.evidence, self.root))

    def test_historical_hash_cannot_cover_updated_rules(self):
        (self.root / FILES[1]).write_bytes(b"changed rules")
        self.assertFalse(module.notification_coverage_valid(self.tests, self.evidence, self.root))

    def test_missing_success_or_wrong_count_cannot_pass(self):
        self.evidence["notification_suite"]["actual_recursive_xunity_consumer_passed"] = False
        self.assertFalse(module.notification_coverage_valid(self.tests, self.evidence, self.root))
        self.evidence["notification_suite"]["actual_recursive_xunity_consumer_passed"] = True
        self.evidence["notification_suite"]["count"] -= 1
        self.assertFalse(module.notification_coverage_valid(self.tests, self.evidence, self.root))


if __name__ == "__main__":
    unittest.main()
