"""核对游戏实际加载的字体坐标、完整纹理及沉字上横，不冒称完整屏幕像素验收。"""

import argparse
import hashlib
import json
import math
from pathlib import Path


def chen_crossbar_present(tile, width, height):
    """检测固定思源字形右侧几部件的上横，区别于最上方冖部件。"""
    if width < 10 or height < 10 or len(tile) != width * height:
        return False
    left, right = int(width * 0.36), int(width * 0.83)
    minimum_run = math.ceil(width * 0.28)
    for row in range(int(height * 0.25), int(height * 0.48)):
        run = 0
        for value in tile[row * width + left:row * width + right]:
            run = run + 1 if value >= 128 else 0
            if run >= minimum_run:
                return True
    return False


def analyze(report, native, runtime_pixels, native_pixels):
    expected = {g["unicode"]: g for g in native["glyphs"]}
    actual = {g["unicode"]: g for g in report.get("glyphs", [])}
    size = native["atlasSize"]
    checks = {"actual_source_han_font_loaded": report.get("font") == "ElsinoreHan Sans SDF",
              "real_distance_field_shader": "Distance Field" in report.get("shader", ""),
              "native_render_mode_and_safe_italic": report.get("renderMode") == 8234 and report.get("italicStyle") == 5,
              "exact_native_atlas_bytes": len(runtime_pixels) == size * size and runtime_pixels == native_pixels,
              "all_requested_glyphs_once": len(actual) == len(report.get("glyphs", [])) == len(expected) and actual.keys() == expected.keys(),
              "all_runtime_rects_and_advance_match": True, "chen_upper_crossbar_present": False}
    for unicode, source in expected.items():
        glyph = actual.get(unicode)
        if glyph is None:
            checks["all_runtime_rects_and_advance_match"] = False
            continue
        checks["all_runtime_rects_and_advance_match"] &= all(glyph[key] == source["rect"][key] for key in ("x", "y", "width", "height"))
        checks["all_runtime_rects_and_advance_match"] &= math.isclose(glyph["advance"], source["advance"], abs_tol=0.00001)
    glyph = actual.get(ord("沉"))
    if glyph is not None and len(runtime_pixels) == size * size:
        x, y, width, height = [glyph[key] for key in ("x", "y", "width", "height")]
        if all(type(v) is int and v >= 0 for v in (x, y, width, height)) and x + width <= size and y + height <= size:
            # Unity原点在左下；笔画检测使用左上原点的字形局部数据。
            tile = b"".join(runtime_pixels[(y + row) * size + x:(y + row) * size + x + width]
                            for row in reversed(range(height)))
            checks["chen_upper_crossbar_present"] = chen_crossbar_present(tile, width, height)
    return {"passed": all(checks.values()), "checks": checks, "glyph_count": len(actual),
            "runtime_atlas_sha256": hashlib.sha256(runtime_pixels).hexdigest(),
            "limitation": "实际字体纹理和glyph坐标核验，不代表完整页面像素、物理按键或全剧情验收"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--bake-directory", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(json.loads((args.evidence / "font-regression.json").read_text(encoding="utf-8")),
                     json.loads((args.bake_directory / "font-bake.json").read_text(encoding="utf-8")),
                     (args.evidence / "font-runtime-atlas.bin").read_bytes(),
                     (args.bake_directory / "font-atlas-alpha8.bin").read_bytes())
    (args.evidence / "font-regression-analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)
