"""真实执行启动前校验，保证缺少采集输入时不会启动游戏或写入副本。"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == "nt", "仅针对本项目Windows启动器")
class PreflightTests(unittest.TestCase):
    def check_rejected(self, variables, expected):
        env = {key: value for key, value in os.environ.items() if not key.startswith("ELSINOREHAN_PROBE_")}
        env.update(variables)
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [shutil.which("pwsh") or "powershell", "-NoProfile", "-NonInteractive", "-File",
                 str(Path(__file__).with_name("run-headless-probe.ps1")), "-GamePath", directory],
                env=env, capture_output=True, timeout=20,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(expected.encode(), result.stdout + result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_italic_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_ITALIC": "1"}, "ELSINOREHAN_PROBE_ITALIC")

    def test_book_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_BOOK_PAGES": "missing.tsv"}, "命运书页回归")

    def test_book_only_without_sources_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_BOOK_ONLY": "1"}, "命运书页专项模式")

    def test_log_scroll_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_LOG_SCROLL": "1"}, "ELSINOREHAN_PROBE_LOG_SCROLL")

    def test_lead_layout_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_LEAD_LAYOUT": "1"}, "任务按钮布局回归")

    def test_document_scroll_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS": "observable_backerbook4"}, "文档阅读位置诊断")

    def test_biography_replay_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_BIOGRAPHY_CASES": "missing.tsv"}, "人物资料重放")

    def test_followup_without_journal_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_UI_FOLLOWUP": "1"}, "ELSINOREHAN_PROBE_UI_FOLLOWUP")

    def test_followup_without_real_lead_cases_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_UI_FOLLOWUP": "1", "ELSINOREHAN_PROBE_JOURNAL": "1"},
                            "ELSINOREHAN_PROBE_UI_FOLLOWUP")

    def test_journal_without_real_document_ids_is_rejected(self):
        self.check_rejected({"ELSINOREHAN_PROBE_JOURNAL": "1"}, "ELSINOREHAN_PROBE_CLOSEUP_IDS")

    def test_missing_cache_input_is_rejected_before_build_or_launch(self):
        self.check_rejected({"ELSINOREHAN_PROBE_CACHE_CASES": str(Path(tempfile.gettempdir()) / "ElsinoreHan-missing-input.tsv")},
                            "ELSINOREHAN_PROBE_CACHE_CASES")

    def test_negative_navigation_delay_is_rejected_before_launch(self):
        self.check_rejected({"ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS": "-1"}, "ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS")

    def test_nonfinite_navigation_delay_is_rejected_before_launch(self):
        self.check_rejected({"ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS": "NaN"}, "ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS")


if __name__ == "__main__":
    unittest.main()
