"""将真实Unity2018引擎生成的思源字形装配为兼容TMP资源，不保留旧字体数据。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime/build/font-audit-deps"))
import UnityPy
from fontTools.ttLib import TTFont

NAME = "ElsinoreHan Sans SDF"
BUNDLE = "elsinorehan_sans_sdf_u2018"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(template, source, bake_directory, output):
    """只复用兼容序列化结构和TMP材质/着色器；图集、字形、metrics均来自新来源。"""
    bake = json.loads((bake_directory / "font-bake.json").read_text(encoding="utf-8"))
    assert bake["engine"] == "Unity2018 FontEngine" and bake["renderMode"] == "SDF8"
    pixels = (bake_directory / "font-atlas-alpha8.bin").read_bytes()
    size, padding = bake["atlasSize"], bake["padding"]
    assert len(pixels) == size * size
    face = bake["face"]
    source_font = TTFont(source)
    source_cmap = source_font.getBestCmap()
    assert all(g["unicode"] in source_cmap and source_font.getGlyphID(source_cmap[g["unicode"]]) == g["index"]
               for g in bake["glyphs"]), "真实引擎字形索引与声明的源字体不符"
    environment = UnityPy.load(str(template))
    bundle = next(iter(environment.files.values()))
    for obj in environment.objects:
        tree = obj.read_typetree()
        if obj.type.name == "Texture2D":
            tree["m_Name"] = NAME + " Atlas"
            tree["m_Width"] = tree["m_Height"] = size
            tree["m_CompleteImageSize"] = len(pixels)
            tree["m_TextureFormat"] = 1
            tree["m_MipCount"] = 1
            tree["m_IsReadable"] = True
            tree["m_StreamData"] = {"offset": 0, "size": 0, "path": ""}
            tree["image data"] = pixels
        elif obj.type.name == "Material":
            tree["m_Name"] = NAME + " Material"
            tree["m_SavedProperties"]["m_Floats"] = [
                (key, padding + 1 if key == "_GradientScale" else size if key in
                 ("_TextureWidth", "_TextureHeight") else value)
                for key, value in tree["m_SavedProperties"]["m_Floats"]]
        elif obj.type.name == "MonoBehaviour":
            assert tree["m_Name"] == "ARIALUNI SDF"
            tree["m_Name"] = NAME
            tree["hashCode"] = tree["materialHashCode"] = 0
            info = tree["m_fontInfo"]
            info.update(Name="ElsinoreHan Sans", PointSize=float(bake["pointSize"]),
                        Scale=face["scale"], CharacterCount=len(bake["glyphs"]),
                        LineHeight=face["lineHeight"], Baseline=face["baseline"],
                        Ascender=face["ascentLine"], CapHeight=face["capLine"],
                        Descender=face["descentLine"], CenterLine=face["capLine"] / 2,
                        SuperscriptOffset=face["ascentLine"], SubscriptOffset=face["descentLine"],
                        Underline=face["underlineOffset"], UnderlineThickness=face["underlineThickness"],
                        strikethrough=face["strikethroughOffset"],
                        strikethroughThickness=face["strikethroughThickness"],
                        TabWidth=4 * next(g["advance"] for g in bake["glyphs"] if g["unicode"] == 32),
                        Padding=float(padding), AtlasWidth=float(size), AtlasHeight=float(size))
            tree["m_glyphInfoList"] = [
                {"id": glyph["unicode"], "x": float(glyph["rect"]["x"]),
                 "y": float(size - glyph["rect"]["y"] - glyph["rect"]["height"]),
                 "width": float(glyph["rect"]["width"]), "height": float(glyph["rect"]["height"]),
                 "xOffset": glyph["bearingX"], "yOffset": glyph["bearingY"],
                 "xAdvance": glyph["advance"], "scale": glyph["scale"]} for glyph in bake["glyphs"]]
            tree["m_kerningInfo"]["kerningPairs"] = []
            tree["m_CreationSettings"].update(sourceFontFileName="SourceHanSansSC-Regular.otf",
                sourceFontFileGUID=digest(source)[:32], referencedFontAssetGUID="", referencedTextAssetGUID="",
                pointSize=bake["pointSize"], padding=padding, atlasWidth=size, atlasHeight=size,
                characterSequence="".join(chr(g["unicode"]) for g in bake["glyphs"]), renderMode=6)
            tree["fallbackFontAssets"] = []
            tree["normalStyle"] = 0
            tree["boldStyle"] = 0.75
            tree["italicStyle"] = 35
        elif obj.type.name == "AssetBundle":
            tree["m_Name"] = tree["m_AssetBundleName"] = BUNDLE
            tree["m_Container"] = [("assets/elsinorehan sans sdf.asset", value)
                                   for _, value in tree["m_Container"]]
        else:
            continue
        obj.save_typetree(tree)
    # 旧resS含Arial图集，必须删除整个资源流，不能仅使Texture2D不再引用它。
    bundle.files = {key: value for key, value in bundle.files.items() if not key.endswith(".resS")}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bundle.save(packer="lz4"))
    rebuilt = UnityPy.load(str(output))
    rebuilt_font = next(obj.read_typetree() for obj in rebuilt.objects if obj.type.name == "MonoBehaviour")
    rebuilt_atlas = next(obj.read() for obj in rebuilt.objects if obj.type.name == "Texture2D")
    assert rebuilt_font["m_Name"] == NAME
    assert rebuilt_atlas.get_image_data() == pixels
    expected_glyphs = tree_glyphs(bake)
    assert len(rebuilt_font["m_glyphInfoList"]) == len(expected_glyphs)
    for actual, expected in zip(rebuilt_font["m_glyphInfoList"], expected_glyphs):
        assert actual.keys() == expected.keys()
        assert all(actual[key] == value if key == "id" else math.isclose(actual[key], value, abs_tol=0.00001)
                   for key, value in expected.items())
    assert not any(key.endswith(".resS") for key in next(iter(rebuilt.files.values())).files)
    proof = {"font_name": NAME, "bundle": BUNDLE, "font_software_license": "OFL-1.1",
             "glyph_generation": bake["engine"], "render_mode": bake["renderMode"],
             "template_sha256": digest(template), "source_font_sha256": digest(source),
             "bake_metadata_sha256": digest(bake_directory / "font-bake.json"),
             "atlas_sha256": hashlib.sha256(pixels).hexdigest(), "bundle_sha256": digest(output),
             "glyph_count": len(bake["glyphs"]), "old_font_atlas_stream_removed": True,
             "old_glyphs_and_kerning_replaced": True, "atlas_bytes_match_real_engine_output": True,
             "all_native_glyph_indexes_match_source_font": True,
             "template_scope": "兼容序列化结构与Unity依赖的TMP材质/着色器，字体数据全部替换"}
    output.with_suffix(".verification.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(proof, ensure_ascii=False))


def tree_glyphs(bake):
    """重读时独立核对每个Unicode、坐标和metrics，允许float序列化精度差异。"""
    size = bake["atlasSize"]
    return [{"id": g["unicode"], "x": float(g["rect"]["x"]),
             "y": float(size - g["rect"]["y"] - g["rect"]["height"]),
             "width": float(g["rect"]["width"]), "height": float(g["rect"]["height"]),
             "xOffset": g["bearingX"], "yOffset": g["bearingY"],
             "xAdvance": g["advance"], "scale": g["scale"]} for g in bake["glyphs"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bake-directory", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=ROOT / "runtime/vendor/fonts/arialuni_sdf_u2018")
    parser.add_argument("--source", type=Path, default=ROOT / "runtime/vendor/fonts/source-han-sans/SourceHanSansSC-Regular.otf")
    parser.add_argument("--output", type=Path, default=ROOT / "runtime/vendor/fonts/elsinorehan_sans_sdf_u2018")
    args = parser.parse_args()
    build(args.template, args.source, args.bake_directory, args.output)
