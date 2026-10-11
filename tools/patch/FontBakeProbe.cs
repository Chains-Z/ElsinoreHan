using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using UnityEngine;
using UnityEngine.TextCore;
using UnityEngine.TextCore.LowLevel;

// 在已建立存档和静音保护的隔离游戏中调用真实Unity2018字形引擎；不打包给用户。
public static class FontBakeProbe
{
    public static IEnumerator Run(string outputDirectory)
    {
        string source = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_FONT_SOURCE");
        string characters = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_FONT_CHARACTERS");
        if (!File.Exists(source) || !File.Exists(characters)) throw new InvalidOperationException("字体生成输入缺失");
        const int size = 8192, pointSize = 56, padding = 6;
        if (FontEngine.InitializeFontEngine() != FontEngineError.Success
            || FontEngine.LoadFontFace(source, pointSize) != FontEngineError.Success)
            throw new InvalidOperationException("真实Unity字体引擎不能加载官方源字体");
        FaceInfo face = FontEngine.GetFaceInfo();
        const BindingFlags binding = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static;
        var getIndex = typeof(FontEngine).GetMethod("GetGlyphIndex", binding, null, new Type[] { typeof(uint) }, null);
        var addGlyphs = typeof(FontEngine).GetMethod("TryAddGlyphsToTexture", binding, null,
            new Type[] { typeof(List<uint>), typeof(int), typeof(GlyphPackingMode), typeof(List<GlyphRect>),
                typeof(List<GlyphRect>), typeof(GlyphRenderMode), typeof(Texture2D), typeof(Glyph[]).MakeByRefType() }, null);
        if (getIndex == null || addGlyphs == null) throw new InvalidOperationException("真实字体引擎签名不符");
        var mapping = new SortedDictionary<uint, uint>();
        var indexes = new SortedSet<uint>();
        foreach (char character in File.ReadAllText(characters, Encoding.UTF8))
        {
            if (character == '\r' || character == '\n') continue;
            uint index = (uint)getIndex.Invoke(null, new object[] { (uint)character });
            if (index == 0) throw new InvalidOperationException("源字体缺字：" + ((int)character).ToString("X4"));
            mapping[character] = index;
            indexes.Add(index);
        }
        var atlas = new Texture2D(size, size, TextureFormat.Alpha8, false);
        atlas.LoadRawTextureData(new byte[size * size]);
        atlas.Apply(false, false);
        var free = new List<GlyphRect> { new GlyphRect(0, 0, size - 1, size - 1) };
        var used = new List<GlyphRect>();
        var packed = new Dictionary<uint, Glyph>();
        var pending = new List<uint>(indexes);
        for (int start = 0; start < pending.Count; start += 64)
        {
            var batch = pending.GetRange(start, Math.Min(64, pending.Count - start));
            var arguments = new object[] { batch, padding, GlyphPackingMode.BestShortSideFit,
                free, used, GlyphRenderMode.SDF8, atlas, null };
            bool complete = (bool)addGlyphs.Invoke(null, arguments);
            var glyphs = (Glyph[])arguments[7];
            if (!complete) throw new InvalidOperationException("字体图集容纳失败，禁止输出不完整资产");
            foreach (Glyph glyph in glyphs)
                if (glyph != null) packed[glyph.index] = glyph;
            Debug.Log("FONT_BAKE_PROGRESS=" + Math.Min(start + 64, pending.Count) + "/" + pending.Count);
            yield return null;
        }
        var json = new StringBuilder();
        json.Append("{\"engine\":\"Unity2018 FontEngine\",\"renderMode\":\"SDF8\",\"pointSize\":56,\"padding\":6,\"atlasSize\":8192,");
        json.Append("\"face\":{");
        Add(json, "lineHeight", face.lineHeight); Add(json, "ascentLine", face.ascentLine);
        Add(json, "capLine", face.capLine); Add(json, "baseline", face.baseline);
        Add(json, "descentLine", face.descentLine); Add(json, "scale", face.scale);
        Add(json, "underlineOffset", face.underlineOffset); Add(json, "underlineThickness", face.underlineThickness);
        Add(json, "strikethroughOffset", face.strikethroughOffset);
        json.Append("\"strikethroughThickness\":").Append(Number(face.strikethroughThickness)).Append("},\"glyphs\":[");
        bool first = true;
        foreach (var entry in mapping)
        {
            Glyph glyph;
            if (!packed.TryGetValue(entry.Value, out glyph)) throw new InvalidOperationException("已请求字形没有生成结果");
            if (!first) json.Append(','); first = false;
            json.Append("{\"unicode\":").Append(entry.Key).Append(",\"index\":").Append(entry.Value).Append(',');
            Add(json, "width", glyph.metrics.width); Add(json, "height", glyph.metrics.height);
            Add(json, "bearingX", glyph.metrics.horizontalBearingX); Add(json, "bearingY", glyph.metrics.horizontalBearingY);
            Add(json, "advance", glyph.metrics.horizontalAdvance); Add(json, "scale", glyph.scale);
            json.Append("\"rect\":{\"x\":").Append(glyph.glyphRect.x).Append(",\"y\":").Append(glyph.glyphRect.y)
                .Append(",\"width\":").Append(glyph.glyphRect.width).Append(",\"height\":").Append(glyph.glyphRect.height).Append("}}");
        }
        json.Append("]}");
        Directory.CreateDirectory(outputDirectory);
        byte[] pixels = atlas.GetRawTextureData();
        if (pixels.Length != size * size) throw new InvalidOperationException("字体图集字节数异常");
        File.WriteAllBytes(Path.Combine(outputDirectory, "font-atlas-alpha8.bin"), pixels);
        File.WriteAllText(Path.Combine(outputDirectory, "font-bake.json"), json.ToString(), new UTF8Encoding(false));
        UnityEngine.Object.Destroy(atlas);
        Debug.Log("FONT_BAKE_COMPLETE=" + mapping.Count);
        Application.Quit();
    }

    private static void Add(StringBuilder json, string name, float value)
    { json.Append('"').Append(name).Append("\":").Append(Number(value)).Append(','); }
    private static string Number(float value) { return value.ToString("R", CultureInfo.InvariantCulture); }
}
