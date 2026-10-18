"""离线加载真实探针和正式插件程序集，回归反射重载与报告数组序列化故障。"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MANAGED = Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed")
COMPILER = Path(os.environ.get("WINDIR", "C:/Windows")) / "Microsoft.NET/Framework/v4.0.30319/csc.exe"
PROBE = ROOT / "runtime/build/ElsinoreHan.RuntimeProbe.dll"
PLUGIN = ROOT / "runtime/build/ElsinoreHan.TranslationToggle.dll"


@unittest.skipUnless(os.name == "nt" and COMPILER.exists() and PROBE.exists() and PLUGIN.exists(),
                     "需要本机.NET编译器及已编译的真实探针、正式插件程序集")
class CreditsSkipProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.executable = Path(cls.temporary.name) / "credits-probe-tests.exe"
        result = subprocess.run(
            [str(COMPILER), "/nologo", "/target:exe", "/platform:x86", "/codepage:65001",
             "/reference:System.Web.Extensions.dll", "/out:" + str(cls.executable),
             str(ROOT / "tools/patch/CreditsSkipProbeTests.cs")], capture_output=True, timeout=30,
        )
        if result.returncode:
            raise RuntimeError("测试CLI编译失败：" + result.stdout.decode(errors="replace")
                               + result.stderr.decode(errors="replace"))

    def run_mode(self, mode):
        result = subprocess.run([str(self.executable), str(ROOT), str(MANAGED), mode],
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(result.stderr, b"")
        return json.loads(result.stdout.decode("utf-8"))

    def test_real_unity_overload_is_ambiguous_and_helper_selects_vertexhelper(self):
        report = self.run_mode("metadata")
        self.assertTrue(report["ambiguous_without_signature"])
        self.assertGreaterEqual(report["overloads"], 2)
        self.assertEqual(report["exact_definitions"], 1)
        self.assertEqual(report["declaring_type"], "CreditsSkipRing")
        self.assertEqual(report["parameter_type"], "UnityEngine.UI.VertexHelper")
        self.assertEqual(report["return_type"], "System.Void")
        self.assertEqual(Path(report["probe_assembly"]).resolve(), PROBE.resolve())
        self.assertEqual(Path(report["plugin_assembly"]).resolve(), PLUGIN.resolve())

    def test_real_report_lists_remain_arrays_and_escape_strings(self):
        report = self.run_mode("report")
        for name in ("checks", "rings", "glyphs"):
            self.assertIsInstance(report[name], list)
            self.assertEqual(len(report[name]), 1)
        self.assertTrue(report["passed"])
        self.assertEqual(report["scene"], 'credits\n"引号"\\路径\t末尾\r\n\x01')
        self.assertEqual(report["label_screen_corners"], [1.25, 2.5])
        self.assertEqual(report["checks"][0], {
            "name": '检查"名称', "detail": '第一行\n第二行\t\\"\x01', "passed": True,
        })
        self.assertEqual(report["rings"][0], {
            "state": "quarter", "progress": 0.25, "minimum_alpha": 1, "maximum_radius": 18,
            "vertices": 34, "triangles": 32, "white": True,
        })
        self.assertEqual(report["glyphs"][0], {
            "character": "长", "font": "ElsinoreHan Sans SDF", "atlas": 'atlas\\"中文',
            "material": 1, "atlas_width": 4096, "atlas_height": 4096, "visible": True, "white": True,
        })

    def test_empty_real_report_lists_are_empty_arrays(self):
        report = self.run_mode("empty-report")
        for name in ("checks", "rings", "glyphs"):
            self.assertEqual(report[name], [])
            self.assertIsInstance(report[name], list)
        self.assertIsNone(report["label_screen_corners"])
        self.assertFalse(report["passed"])

    def test_cli_catches_failure_and_reports_only_to_terminal(self):
        result = subprocess.run([str(self.executable), "--check-error-handler"],
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"InvalidOperationException:", result.stderr)


if __name__ == "__main__":
    unittest.main()
