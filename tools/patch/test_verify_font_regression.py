"""上横缺失与错误纹理/字形映射的局部门禁回归，不模拟真实游戏验收。"""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("font_regression", Path(__file__).with_name("verify-font-regression.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FontRegressionTests(unittest.TestCase):
    def test_missing_chen_bar_cannot_pass(self):
        tile = bytearray(20 * 20)
        for x in range(7, 16):
            tile[6 * 20 + x] = 255
        self.assertTrue(module.chen_crossbar_present(tile, 20, 20))
        for x in range(7, 16):
            tile[6 * 20 + x] = 0
        self.assertFalse(module.chen_crossbar_present(tile, 20, 20))

    def test_top_cover_cannot_substitute_for_missing_bar(self):
        tile = bytearray(20 * 20)
        for x in range(7, 16):
            tile[1 * 20 + x] = 255
        self.assertFalse(module.chen_crossbar_present(tile, 20, 20))

    def test_wrong_runtime_font_and_atlas_cannot_pass(self):
        result = module.analyze({"font": "ARIALUNI SDF", "glyphs": []},
                                {"atlasSize": 8192, "glyphs": []}, b"incorrect", b"source")
        self.assertFalse(result["checks"]["actual_source_han_font_loaded"])
        self.assertFalse(result["checks"]["exact_native_atlas_bytes"])
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
