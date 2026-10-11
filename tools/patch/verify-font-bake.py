"""核对真实字体引擎产物，完成标记读取player.log而非BepInEx日志。"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


def analyze(data, characters, pixel_bytes, player_log):
    """拒绝缺字、重复Unicode、越界坐标、空图集及只有中间进度的输出。"""
    glyphs = data.get("glyphs", [])
    expected = {ord(c) for c in characters if c not in "\r\n"}
    size = data.get("atlasSize")
    valid_size = type(size) is int and size == 8192
    actual = [g.get("unicode") for g in glyphs]
    finite = lambda value: type(value) in (int, float) and math.isfinite(value)
    checks = {
        "real_engine_and_mode": data.get("engine") == "Unity2018 FontEngine" and data.get("renderMode") == "SDF8",
        "native_sampling_and_padding": data.get("pointSize") == 56 and data.get("padding") == 6,
        "exact_unique_unicode_set": len(actual) == len(expected) and set(actual) == expected,
        "exact_alpha8_length": valid_size and len(pixel_bytes) == size * size,
        "actual_completion_marker": re.search(r"(?m)^FONT_BAKE_COMPLETE=" + str(len(expected)) + r"\s*$", player_log) is not None,
        "finite_metrics_and_in_bounds": bool(glyphs),
        "all_visible_glyphs_have_ink": bool(glyphs),
    }
    for glyph in glyphs:
        rect = glyph.get("rect", {})
        rectangle = [rect.get(k) for k in ("x", "y", "width", "height")]
        valid = valid_size and all(type(v) is int and v >= 0 for v in rectangle)
        if valid:
            x, y, width, height = rectangle
            valid = x + width <= size and y + height <= size
        valid &= all(finite(glyph.get(k)) for k in ("width", "height", "bearingX", "bearingY", "advance", "scale"))
        valid &= type(glyph.get("index")) is int and glyph["index"] > 0
        checks["finite_metrics_and_in_bounds"] &= valid
        if valid and width and height and len(pixel_bytes) == size * size:
            checks["all_visible_glyphs_have_ink"] &= any(
                max(pixel_bytes[(y + row) * size + x:(y + row) * size + x + width], default=0) >= 128
                for row in range(height))
        elif not valid:
            checks["all_visible_glyphs_have_ink"] = False
    return {"passed": all(checks.values()), "checks": checks, "character_count": len(expected),
            "atlas_sha256": hashlib.sha256(pixel_bytes).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--characters", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(json.loads((args.evidence / "font-bake.json").read_text(encoding="utf-8")),
                     args.characters.read_text(encoding="utf-8"),
                     (args.evidence / "font-atlas-alpha8.bin").read_bytes(),
                     (args.evidence / "player.log").read_text(encoding="utf-8-sig"))
    (args.evidence / "font-bake-verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)
