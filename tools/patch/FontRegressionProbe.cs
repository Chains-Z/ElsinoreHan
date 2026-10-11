using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMPro;

// 读取实际加载的字形与纹理，防止只验证源字体而漏掉AssetBundle装配问题。
public static class FontRegressionProbe
{
    [Serializable] public sealed class GlyphRecord
    {
        public int unicode, x, y, width, height;
        public float advance;
    }
    [Serializable] public sealed class Report
    {
        public string font, shader, version;
        public int atlasWidth, atlasHeight, renderMode, italicStyle;
        public GlyphRecord[] glyphs;
    }

    public static void Capture(TMP_FontAsset font, string directory)
    {
        string input = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_FONT_CHARACTERS");
        if (font.name != "ElsinoreHan Sans SDF" || string.IsNullOrEmpty(input)) return;
        if (font.material == null || font.material.shader == null) throw new InvalidOperationException("中文字体材质未加载");
        var glyphs = new List<GlyphRecord>();
        var seen = new HashSet<char>();
        foreach (char character in File.ReadAllText(input, Encoding.UTF8))
        {
            if (character == '\r' || character == '\n' || !seen.Add(character)) continue;
            TMP_Character entry;
            if (!font.characterLookupTable.TryGetValue(character, out entry))
                throw new InvalidOperationException("实际字体缺字：" + ((int)character).ToString("X4"));
            var glyph = entry.glyph;
            glyphs.Add(new GlyphRecord { unicode = character, x = glyph.glyphRect.x, y = glyph.glyphRect.y,
                width = glyph.glyphRect.width, height = glyph.glyphRect.height, advance = glyph.metrics.horizontalAdvance });
        }
        var report = new Report { font = font.name, shader = font.material.shader.name, version = font.version,
            atlasWidth = font.atlasWidth, atlasHeight = font.atlasHeight,
            renderMode = (int)font.atlasRenderMode, italicStyle = font.italicStyle, glyphs = glyphs.ToArray() };
        Directory.CreateDirectory(directory);
        File.WriteAllText(Path.Combine(directory, "font-regression.json"), ItalicGeometryProbe.Serialize(report), new UTF8Encoding(false));
        File.WriteAllBytes(Path.Combine(directory, "font-runtime-atlas.bin"), font.atlasTextures[0].GetRawTextureData());
    }
}
