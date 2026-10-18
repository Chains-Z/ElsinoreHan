"""编译真实片尾Ctrl手势类，验证长按、防误触与异常边界；不启动游戏。"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
COMPILER = Path(os.environ.get("WINDIR", "C:/Windows")) / "Microsoft.NET/Framework/v4.0.30319/csc.exe"
CASES = (
    "half_progress_stall_resumes", "release_after_stall_cancels",
    "focus_after_stall_cancels", "normal_frame_rates_keep_hold_duration",
    "loading_hold_starts_at_zero_when_visible", "preheld_loading_still_requires_release",
    "release_during_loading_cancels_pending_hold", "presentation_loss_discards_elapsed_time",
    "short_press", "one_second_boundary", "quarter_and_half_progress", "release_cancels_progress",
    "held_on_entry_requires_release", "focus_loss_cancels", "focus_return_requires_fresh_press",
    "one_shot", "reset_starts_new_round", "clock_rollback_restarts", "clock_rollback_after_progress",
    "subsecond_rounding_cannot_trigger", "nan_time",
    "positive_infinity", "negative_infinity", "negative_time", "inactive_cancels",
    "inactive_cannot_arm", "long_frame_clamps_progress", "reset_clears_partial_hold",
)


@unittest.skipUnless(os.name == "nt" and COMPILER.exists(), "需要本机.NET Framework编译器")
class CreditsSkipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.executable = Path(cls.temporary.name) / "credits-gesture.exe"
        result = subprocess.run(
            [str(COMPILER), "/nologo", "/target:exe", "/out:" + str(cls.executable),
             str(ROOT / "tools/patch/CreditsSkipGesture.cs"),
             str(ROOT / "tools/patch/CreditsSkipGestureTests.cs")],
            capture_output=True, timeout=30,
        )
        if result.returncode:
            raise RuntimeError("纯逻辑测试编译失败：" + result.stdout.decode(errors="replace")
                               + result.stderr.decode(errors="replace"))

    def run_case(self, name):
        result = subprocess.run([str(self.executable), name], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(json.loads(result.stdout), {"pure_cases": 1, "passed": True})
        self.assertEqual(result.stderr, b"")

    def test_cli_reports_exceptions_without_unhandled_crash(self):
        result = subprocess.run([str(self.executable), "--check-error-handler"],
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"InvalidOperationException:", result.stderr)


def case_test(name):
    def test(self):
        self.run_case(name)
    test.__doc__ = "真实C#手势行为：" + name
    return test


for case in CASES:
    setattr(CreditsSkipTests, "test_" + case, case_test(case))


if __name__ == "__main__":
    unittest.main()
