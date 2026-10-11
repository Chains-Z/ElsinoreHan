"""墨迹覆盖范围与任务布局验证器的回归测试。"""
import base64
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('verify_lead_layout', ROOT / 'tools/patch/verify-lead-layout.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def sample() -> str:
    """验证器局部夹具，不冒充游戏页面证据。"""
    rows = ['EXPECTED\t2\t8']
    for mode in range(8):
        for index in range(2):
            text = '任务' + str(index) if mode % 2 == 0 else 'Quest ' + str(index)
            encoded = base64.b64encode(text.encode()).decode()
            rows.append('\t'.join(map(str, ['ITEM', mode, index, encoded, 36, 282, 90, 9, -153, 153, 0] + ['True'] * 8)))
    return '\n'.join(rows + ['STATUS\tCOMPLETE'])


class LayoutValidationTests(unittest.TestCase):
    def test_complete(self):
        self.assertTrue(verifier.analyze(sample())['passed'])

    def test_old_background_cannot_cover_english(self):
        self.assertFalse(verifier.analyze(sample().replace('\tTrue\tTrue', '\tFalse\tTrue', 1))['passed'])

    def test_missing_mode(self):
        rows = sample().splitlines()
        del rows[3]
        self.assertFalse(verifier.analyze('\n'.join(rows))['passed'])

    def test_font_change(self):
        self.assertFalse(verifier.analyze(sample().replace('\t36\t', '\t40\t', 1))['passed'])

    def test_duplicate_listener(self):
        rows = sample().splitlines()
        values = rows[1].split('\t')
        values[17] = 'False'
        rows[1] = '\t'.join(values)
        self.assertFalse(verifier.analyze('\n'.join(rows))['passed'])

    def test_failure_not_complete(self):
        self.assertFalse(verifier.analyze(sample().replace('STATUS\tCOMPLETE', 'STATUS\tFAILED'))['passed'])

    def test_actual_geometry_algorithm(self):
        compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory(dir=ROOT / 'runtime/build') as directory:
            source = Path(directory) / 'Test.cs'
            output = Path(directory) / 'Test.exe'
            source.write_text('''using System;
class Test {
    static int Main() {
        float[] widths = {60, 90, 90.1f, 282.01f, 397.76f};
        int[] expected = {1, 1, 2, 9, 13};
        for (int i = 0; i < widths.Length; i++)
            if (SplotchTileGeometry.Count(widths[i], 90) != expected[i]) return 1;
        for (int w = 30; w <= 800; w++) {
            int count = SplotchTileGeometry.Count(w, 90);
            float left = SplotchTileGeometry.Center(0, count, 90) - 45;
            float right = SplotchTileGeometry.Center(count - 1, count, 90) + 45;
            if (right - left + 0.001f < w || Math.Abs(left + right) > 0.001f) return 2;
        }
        try { SplotchTileGeometry.Count(100, 0); return 3; }
        catch (ArgumentOutOfRangeException) {}
        return 0;
    }
}''', encoding='utf-8')
            subprocess.run([str(compiler), '/nologo', '/target:exe', '/out:' + str(output),
                            str(ROOT / 'tools/patch/SplotchTileGeometry.cs'), str(source)], check=True, capture_output=True)
            subprocess.run([str(output)], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
