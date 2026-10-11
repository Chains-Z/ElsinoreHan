"""覆盖完成标记落在player.log以及缺字/空图集不能通过的生成门禁。"""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("verify_font_bake", Path(__file__).with_name("verify-font-bake.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FontBakeTests(unittest.TestCase):
    def test_player_log_completion_is_required_even_with_all_glyphs(self):
        data = {"engine": "Unity2018 FontEngine", "renderMode": "SDF8", "pointSize": 56,
                "padding": 6, "atlasSize": 8192, "glyphs": []}
        result = module.analyze(data, "", b"", "FONT_BAKE_PROGRESS=0/0\n")
        self.assertFalse(result["checks"]["actual_completion_marker"])
        result = module.analyze(data, "", b"", "FONT_BAKE_COMPLETE=0\n")
        self.assertTrue(result["checks"]["actual_completion_marker"])
        self.assertFalse(result["passed"])

    def test_completion_for_another_count_cannot_pass(self):
        result = module.analyze({}, "沉", b"", "FONT_BAKE_COMPLETE=2\n")
        self.assertFalse(result["checks"]["actual_completion_marker"])
        self.assertFalse(result["checks"]["exact_unique_unicode_set"])

    def test_duplicate_unicode_and_out_of_bounds_are_rejected(self):
        glyph = {"unicode": ord("沉"), "index": 1, "width": 1, "height": 1,
                 "bearingX": 0, "bearingY": 1, "advance": 1, "scale": 1,
                 "rect": {"x": 8192, "y": 0, "width": 1, "height": 1}}
        result = module.analyze({"atlasSize": 8192, "glyphs": [glyph, glyph]}, "沉", b"", "")
        self.assertFalse(result["checks"]["exact_unique_unicode_set"])
        self.assertFalse(result["checks"]["finite_metrics_and_in_bounds"])


if __name__ == "__main__":
    unittest.main()
