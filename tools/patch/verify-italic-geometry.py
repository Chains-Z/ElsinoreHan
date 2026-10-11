"""验证中文斜体组件网格，不将SDF外边框或组件测试称为像素/剧情E2E。"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SOURCE_TEXTS = {
    "p10804-e0f7f605aeb5": "他什么时候<i>不</i>古怪了？不过，我想这也说得通。",
    "p10805-9c05de9c31a3": "我相信，那么多人里，他<i>当然会</i>找你寻求安慰，在……呃……之后。",
}
SOURCE_IDS = set(SOURCE_TEXTS)


def finite(value):
    """拒绝布尔值、字符串和非有限数值混入几何证据。"""
    return type(value) in (int, float) and math.isfinite(value)


def expected_characters(source):
    """冻结样本只有一段斜体；将富文本位置转换为实际字符位置。"""
    before, rest = SOURCE_TEXTS[source].split("<i>")
    emphasized, after = rest.split("</i>")
    return before + emphasized + after, set(range(len(before), len(before) + len(emphasized)))


def boundary_evidence_valid(sample):
    """由真实同排相邻字符推导所有强调边界，避免独立gap字段冒充网格。"""
    characters, boundaries = sample.get("characters"), sample.get("boundaries")
    if not isinstance(characters, list) or not isinstance(boundaries, list):
        return False
    if any(not isinstance(c, dict) for c in characters):
        return False
    expected = [(a, b) for a, b in zip(characters, characters[1:])
                if a.get("line") == b.get("line") and a.get("italic") != b.get("italic")]
    if len(boundaries) != len(expected):
        return False
    for boundary, (left, right) in zip(boundaries, expected):
        if not isinstance(boundary, dict) or not finite(boundary.get("gap")):
            return False
        if (type(boundary.get("left")) is not int or type(boundary.get("right")) is not int
                or boundary["left"] != left.get("index") or boundary["right"] != right.get("index")):
            return False
        if not finite(left.get("inkRight")) or not finite(right.get("inkLeft")):
            return False
        if abs(boundary["gap"] - (right["inkLeft"] - left["inkRight"])) > 0.01:
            return False
    return True


def analyze(report: dict, font_name: str = "ARIALUNI SDF") -> dict:
    """检查真实字形包络、剪切保留及不改字符推进的局部回归。"""
    samples = report.get("samples", [])
    valid_samples = isinstance(samples, list) and all(isinstance(s, dict) for s in samples)
    samples = samples if valid_samples else []
    keyed = {(s["layout"], s["sourceId"], s["mode"]): s for s in samples
             if all(isinstance(s.get(field), str) for field in ("layout", "sourceId", "mode"))}
    expected = {(layout, source, mode) for layout in ("dialogue", "log")
                for source in SOURCE_IDS for mode in ("old", "repaired", "normal")}
    checks = {
        "schema_valid": report.get("schema") == 1,
        "font_restored": report.get("fontRestored") is True,
        "actual_old_style_recorded": type(report.get("originalItalicStyle")) is int
        and report["originalItalicStyle"] == 35,
        "repaired_style_expected": type(report.get("repairedItalicStyle")) is int
        and report["repairedItalicStyle"] == (5 if font_name == "ElsinoreHan Sans SDF" else 10),
        "all_twelve_samples": valid_samples and set(keyed) == expected and len(samples) == 12,
        "nonempty_character_samples": bool(samples),
        "mode_style_consistent": True,
        "layout_geometry_consistent": True,
        "expected_text_and_emphasis": True,
        "boundary_evidence_valid": True,
        "all_geometry_finite": True,
        "both_boundaries_recorded": True,
        "repaired_ink_boundaries_clear": True,
        "italic_retained": True,
        "normal_not_slanted": True,
        "character_advance_unchanged": True,
        "slant_reduced": True,
        "boundary_gaps_improved": True,
        "old_collision_reproduced": False,
    }
    comparisons = []
    for layout in ("dialogue", "log"):
        for source in sorted(SOURCE_IDS):
            if any((layout, source, mode) not in keyed for mode in ("old", "repaired", "normal")):
                continue
            old, repaired, normal = (keyed[layout, source, mode] for mode in ("old", "repaired", "normal"))
            group = old, repaired, normal
            usable = all(isinstance(s.get("characters"), list) and bool(s["characters"])
                         and all(isinstance(c, dict) for c in s["characters"])
                         and isinstance(s.get("boundaries"), list)
                         and all(isinstance(b, dict) for b in s["boundaries"]) for s in group)
            checks["nonempty_character_samples"] &= usable
            if not usable:
                continue
            old_chars, repaired_chars, normal_chars = (s["characters"] for s in group)
            checks["mode_style_consistent"] &= all(
                type(s.get("italicStyle")) is int and s["italicStyle"] == style
                for s, style in zip(group, (report.get("originalItalicStyle"),
                                           report.get("repairedItalicStyle"), report.get("repairedItalicStyle")))
            )
            for field in ("width", "fontSize"):
                values = [s.get(field) for s in group]
                checks["layout_geometry_consistent"] &= all(finite(v) and v > 0 for v in values)
                if all(finite(v) for v in values):
                    checks["layout_geometry_consistent"] &= max(values) - min(values) < 0.01
            plain, emphasized_indices = expected_characters(source)
            for sample in group:
                expected_text = plain if sample["mode"] == "normal" else SOURCE_TEXTS[source]
                characters = sample["characters"]
                checks["expected_text_and_emphasis"] &= sample.get("text") == expected_text and len(characters) == len(plain)
                for index, character in enumerate(characters):
                    checks["expected_text_and_emphasis"] &= (
                        index < len(plain) and character.get("text") == plain[index]
                        and type(character.get("index")) is int and character["index"] == index
                        and type(character.get("line")) is int and character["line"] >= 0
                        and type(character.get("italic")) is bool
                        and character["italic"] == (sample["mode"] != "normal" and index in emphasized_indices)
                    )
                checks["boundary_evidence_valid"] &= boundary_evidence_valid(sample)
            checks["all_geometry_finite"] &= all(
                finite(c.get(field)) for s in group
                for c in s["characters"] for field in ("origin", "advance", "inkLeft", "inkRight", "tilt")
            )
            checks["all_geometry_finite"] &= all(
                finite(b.get("gap")) for s in group for b in s["boundaries"]
            )
            if not all(finite(c.get(field)) for s in group for c in s["characters"]
                       for field in ("origin", "advance", "inkLeft", "inkRight", "tilt")):
                continue
            checks["all_geometry_finite"] &= all(c["inkLeft"] <= c["inkRight"] for s in group for c in s["characters"])
            if not all(finite(b.get("gap")) for s in group for b in s["boundaries"]):
                continue
            checks["both_boundaries_recorded"] &= len(old["boundaries"]) == len(repaired["boundaries"]) == 2
            checks["repaired_ink_boundaries_clear"] &= bool(repaired["boundaries"]) and all(
                b["gap"] >= -0.05 for b in repaired["boundaries"]
            )
            old_collision = any(b["gap"] < -0.05 for b in old["boundaries"])
            checks["old_collision_reproduced"] |= old_collision
            emphasized = [c for c in repaired_chars if c.get("italic")]
            checks["italic_retained"] &= bool(emphasized) and all(
                c.get("font") == font_name and abs(c["tilt"]) > 0.01 for c in emphasized
            )
            checks["normal_not_slanted"] &= bool(normal_chars) and all(
                not c.get("italic") and abs(c["tilt"]) < 0.01 for c in normal_chars
            )
            checks["character_advance_unchanged"] &= len(old_chars) == len(repaired_chars) == len(normal_chars)
            for a, b, c in zip(old_chars, repaired_chars, normal_chars):
                checks["character_advance_unchanged"] &= a.get("text") == b.get("text") == c.get("text") and all(
                    abs(a[field] - b[field]) < 0.01 and abs(b[field] - c[field]) < 0.01
                    for field in ("origin", "advance")
                )
                checks["character_advance_unchanged"] &= a.get("line") == b.get("line") == c.get("line")
                if b.get("italic"):
                    checks["slant_reduced"] &= abs(a["tilt"]) > abs(b["tilt"]) > 0.01
            if any(type(b.get(field)) is not int for s in group for b in s["boundaries"]
                   for field in ("left", "right")):
                continue
            old_edges = {(b["left"], b["right"]): b["gap"] for b in old["boundaries"]}
            for boundary in repaired["boundaries"]:
                key = boundary.get("left"), boundary.get("right")
                checks["boundary_gaps_improved"] &= key in old_edges and boundary["gap"] >= old_edges[key] - 0.01
            comparisons.append({"layout": layout, "source_id": source,
                                "old_min_gap": min((b["gap"] for b in old["boundaries"]), default=None),
                                "repaired_min_gap": min((b["gap"] for b in repaired["boundaries"]), default=None)})
    return {"passed": all(checks.values()), "checks": checks, "comparisons": comparisons,
            "scope": report.get("scope"), "limitation": report.get("limitation")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--font", default="ARIALUNI SDF")
    args = parser.parse_args()
    result = analyze(json.loads(args.report.read_text(encoding="utf-8-sig")), args.font)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
