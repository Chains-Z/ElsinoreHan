"""防止编译失败后继续运行旧测试程序。"""

import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("invited_runner", Path(__file__).with_name("verify-invited-event-notice.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class InvitedValidationRunnerTests(unittest.TestCase):
    def test_failed_compilation_rejects_existing_old_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "old.exe"
            executable.write_bytes(b"old")
            with patch.object(runner, "quiet_run") as launch:
                with self.assertRaises(RuntimeError):
                    runner.run_compiled_test(SimpleNamespace(returncode=1), executable, [])
                launch.assert_not_called()

    def test_missing_successful_output_rejects_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runner, "quiet_run") as launch:
                with self.assertRaises(RuntimeError):
                    runner.run_compiled_test(SimpleNamespace(returncode=0), Path(directory) / "absent.exe", [])
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
