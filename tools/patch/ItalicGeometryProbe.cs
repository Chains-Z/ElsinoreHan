using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Globalization;
using System.Text;
using TMPro;
using UnityEngine;

// 只在隔离探针中比较真实字体网格；使用冻结译文的组件局部验证，不执行剧情。
public static class ItalicGeometryProbe
{
    [Serializable] public sealed class Point { public float x, y; public Point(Vector3 p) { x = p.x; y = p.y; } }
    [Serializable] public sealed class Character
    {
        public int index, line; public string text, font; public bool italic;
        public float origin, advance, inkLeft, inkRight, tilt;
        public Point[] quad;
    }
    [Serializable] public sealed class Boundary { public int left, right; public float gap; }
    [Serializable] public sealed class Sample
    {
        public string layout, sourceId, mode, text, templatePath;
        public int italicStyle; public float fontSize, width;
        public Character[] characters; public Boundary[] boundaries;
    }
    [Serializable] public sealed class Report
    {
        public int schema = 1, originalItalicStyle, repairedItalicStyle = 10;
        public string scope = "真实对白/日志字体参数的冻结译文单行网格局部测试";
        public string layoutMethod = "后台Canvas没有屏幕布局；隔离样本禁用换行和裁切以完整比较相邻字，不验收实际页面换行";
        public string boundsMethod = "实际网格顶点/UV映射到字体glyph矩形，排除SDF padding";
        public string limitation = "glyph矩形为字形metrics包络；未采样纹理alpha，不能替代像素目测";
        public bool fontRestored; public Sample[] samples;
    }
    private static readonly string[] SourceIds = { "p10804-e0f7f605aeb5", "p10805-9c05de9c31a3" };
    private static readonly string[] Texts = {
        "他什么时候<i>不</i>古怪了？不过，我想这也说得通。",
        "我相信，那么多人里，他<i>当然会</i>找你寻求安慰，在……呃……之后。"
    };

    public static bool TryCapture(string outputDirectory)
    {
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_ITALIC") != "1") return true;
        TextMeshProUGUI dialogue = null, log = null;
        var catalogue = new System.Text.StringBuilder();
        foreach (TextMeshProUGUI text in Resources.FindObjectsOfTypeAll<TextMeshProUGUI>())
        {
            if (!text.gameObject.scene.IsValid() || !text.gameObject.scene.isLoaded) continue;
            string path = PathOf(text.transform);
            if (path.IndexOf("dialog", StringComparison.OrdinalIgnoreCase) >= 0 || path.IndexOf("log", StringComparison.OrdinalIgnoreCase) >= 0)
                catalogue.AppendLine(path + " width=" + text.rectTransform.rect.width + " font=" + (text.font == null ? "null" : text.font.name));
            if ((path.Contains("LogGroup(Clone)") || path.Contains("Log(Clone)")) && text.gameObject.activeInHierarchy && text.rectTransform.rect.width > 100f && log == null) log = text;
            if (text.name == "DialogueText" && text.rectTransform.rect.width > 100f) dialogue = text;
        }
        if (dialogue == null || log == null)
        {
            Directory.CreateDirectory(outputDirectory);
            File.WriteAllText(System.IO.Path.Combine(outputDirectory, "italic-template-catalog.txt"), catalogue.ToString());
            throw new InvalidOperationException("字体几何模板缺失：dialogue=" + (dialogue != null) + " log=" + (log != null));
        }
        TMP_FontAsset chinese = null;
        foreach (TMP_FontAsset font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            if (font.name == "ARIALUNI SDF") { chinese = font; break; }
        if (chinese == null)
        {
            foreach (TMP_FontAsset font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>()) catalogue.AppendLine("FONT=" + font.name);
            File.WriteAllText(System.IO.Path.Combine(outputDirectory, "italic-template-catalog.txt"), catalogue.ToString());
            throw new InvalidOperationException("未定位实际中文字体资产");
        }
        byte? original = OriginalStyle();
        if (!original.HasValue) throw new InvalidOperationException("无法读取中文字体修复前的真实斜体剪切值");
        var report = new Report { originalItalicStyle = original.Value };
        var samples = new List<Sample>();
        // 三种网格必须在同一次同步调用中采集，finally恢复字体，禁止跨帧改变别的控件。
        try
        {
            TextMeshProUGUI[] templates = { dialogue, log };
            string[] layouts = { "dialogue", "log" };
            for (int layout = 0; layout < templates.Length; layout++)
                for (int sentence = 0; sentence < Texts.Length; sentence++)
                {
                    samples.Add(Capture(templates[layout], log.transform.parent, layouts[layout], sentence, "old", original.Value, chinese));
                    samples.Add(Capture(templates[layout], log.transform.parent, layouts[layout], sentence, "repaired", 10, chinese));
                    samples.Add(Capture(templates[layout], log.transform.parent, layouts[layout], sentence, "normal", 10, chinese));
                }
        }
        finally { chinese.italicStyle = 10; report.fontRestored = chinese.italicStyle == 10; }
        report.samples = samples.ToArray();
        Directory.CreateDirectory(outputDirectory);
        // 本机 Unity 的 JsonUtility 会漏掉动态加载探针中的嵌套数组，显式导出全部字段。
        var json = new StringBuilder();
        WriteJson(json, report);
        File.WriteAllText(System.IO.Path.Combine(outputDirectory, "italic-geometry.json"), json.ToString(), new UTF8Encoding(false));
        return true;
    }

    private static void WriteJson(StringBuilder output, object value)
    {
        if (value == null) { output.Append("null"); return; }
        if (value is string)
        {
            output.Append('"');
            foreach (char ch in (string)value)
            {
                if (ch == '"' || ch == '\\') output.Append('\\').Append(ch);
                else if (ch < 32) output.Append("\\u").Append(((int)ch).ToString("x4"));
                else output.Append(ch);
            }
            output.Append('"'); return;
        }
        if (value is bool) { output.Append((bool)value ? "true" : "false"); return; }
        if (value is float) { output.Append(((float)value).ToString("R", CultureInfo.InvariantCulture)); return; }
        if (value is int || value is byte) { output.Append(Convert.ToString(value, CultureInfo.InvariantCulture)); return; }
        var array = value as Array;
        if (array != null)
        {
            output.Append('[');
            for (int i = 0; i < array.Length; i++)
            {
                if (i > 0) output.Append(',');
                WriteJson(output, array.GetValue(i));
            }
            output.Append(']'); return;
        }
        output.Append('{');
        bool first = true;
        foreach (var field in value.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            if (!first) output.Append(','); first = false;
            WriteJson(output, field.Name); output.Append(':'); WriteJson(output, field.GetValue(value));
        }
        output.Append('}');
    }

    private static byte? OriginalStyle()
    {
        foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            Type type = assembly.GetType("TranslationToggle", false);
            if (type == null) continue;
            FieldInfo field = type.GetField("OriginalChineseItalicStyle", BindingFlags.Public | BindingFlags.Static);
            object value = field == null ? null : field.GetValue(null);
            if (value != null) return Convert.ToByte(value);
        }
        return null;
    }

    private static Sample Capture(TextMeshProUGUI template, Transform activeParent, string layout, int sentence, string mode, byte style, TMP_FontAsset chinese)
    {
        if (!activeParent.gameObject.activeInHierarchy)
            throw new InvalidOperationException("几何采集父级没有激活的Canvas");
        var obj = new GameObject("ElsinoreHanItalicGeometry", typeof(RectTransform));
        // TMP 1.4 的 ForceMeshUpdate(true) 仍要求 Canvas；隐藏对白父级不能提供它。
        // 使用当前日志的活跃父级，并冻结模板矩形，保证三种模式比较同一尺寸。
        obj.transform.SetParent(activeParent, false);
        var rect = (RectTransform)obj.transform;
        rect.anchorMin = rect.anchorMax = new Vector2(0.5f, 0.5f);
        rect.pivot = template.rectTransform.pivot; rect.sizeDelta = template.rectTransform.rect.size;
        rect.anchoredPosition = template.rectTransform.anchoredPosition;
        rect.localScale = template.rectTransform.localScale;
        var clone = obj.AddComponent<TextMeshProUGUI>();
        try
        {
            clone.font = template.font; clone.fontSharedMaterial = template.fontSharedMaterial;
            clone.fontSize = template.fontSize; clone.fontStyle = template.fontStyle & ~FontStyles.Italic;
            clone.enableAutoSizing = template.enableAutoSizing;
            clone.fontSizeMin = template.fontSizeMin; clone.fontSizeMax = template.fontSizeMax;
            // -nographics 的模板矩形尚未按屏幕展开；消除样本换行/裁切，完整检验最坏相邻字距。
            // 只改临时样本，游戏组件和实际页面的换行配置保持原样。
            clone.enableWordWrapping = false; clone.overflowMode = TextOverflowModes.Overflow;
            clone.alignment = template.alignment; clone.margin = template.margin;
            clone.characterSpacing = template.characterSpacing; clone.wordSpacing = template.wordSpacing;
            clone.lineSpacing = template.lineSpacing; clone.paragraphSpacing = template.paragraphSpacing;
            clone.richText = true; clone.raycastTarget = false;
            // 先确保fallback字体定义已加载，避免ReadFontAssetDefinition补丁改回当前测试值。
            clone.text = Texts[sentence]; clone.ForceMeshUpdate(true);
            chinese.italicStyle = style;
            clone.text = mode == "normal" ? Texts[sentence].Replace("<i>", "").Replace("</i>", "") : Texts[sentence];
            clone.havePropertiesChanged = true; clone.ForceMeshUpdate(true);
            if (chinese.italicStyle != style) throw new InvalidOperationException("采集期间斜体参数被重写");
            if (clone.textInfo == null || clone.textInfo.characterCount == 0)
                throw new InvalidOperationException("字体几何克隆未生成字符网格：" + layout + "/" + mode);
            var chars = new List<Character>();
            for (int i = 0; i < clone.textInfo.characterCount; i++)
            {
                TMP_CharacterInfo info = clone.textInfo.characterInfo[i];
                if (!info.isVisible) continue;
                if (info.fontAsset == null || (info.character >= '\u4e00' && info.character <= '\u9fff' && info.fontAsset.name != "ARIALUNI SDF"))
                    throw new InvalidOperationException("几何样本没有使用目标中文字体：" + info.character);
                var mesh = clone.textInfo.meshInfo[info.materialReferenceIndex];
                int vertex = info.vertexIndex;
                var quad = new Point[4];
                for (int corner = 0; corner < 4; corner++) quad[corner] = new Point(mesh.vertices[vertex + corner]);
                // 本机TMP使用TextCore字符元素，实际lookup key为uint，不是旧TMP_Glyph/int字典。
                // SaveGlyphVertexInfo直接使用GlyphRect.y/atlasHeight，原点在纹理下方，不翻转y。
                object glyph = Read(Read(Read(info, "textElement"), "glyph"), "glyphRect");
                float atlasWidth = Number(info.fontAsset, "atlasWidth"), atlasHeight = Number(info.fontAsset, "atlasHeight");
                float u0 = Number(glyph, "x") / atlasWidth, u1 = (Number(glyph, "x") + Number(glyph, "width")) / atlasWidth;
                float v0 = Number(glyph, "y") / atlasHeight;
                float v1 = (Number(glyph, "y") + Number(glyph, "height")) / atlasHeight;
                Vector2 uvBL = mesh.uvs0[vertex], uvTR = mesh.uvs0[vertex + 2];
                float left = float.PositiveInfinity, right = float.NegativeInfinity;
                Vector3 topLeft = Vector3.zero, bottomLeft = Vector3.zero;
                for (int corner = 0; corner < 4; corner++)
                {
                    float u = (corner < 2 ? u0 : u1), v = (corner == 0 || corner == 3 ? v0 : v1);
                    float tx = (u - uvBL.x) / (uvTR.x - uvBL.x), ty = (v - uvBL.y) / (uvTR.y - uvBL.y);
                    Vector3 bottom = Vector3.LerpUnclamped(mesh.vertices[vertex], mesh.vertices[vertex + 3], tx);
                    Vector3 top = Vector3.LerpUnclamped(mesh.vertices[vertex + 1], mesh.vertices[vertex + 2], tx);
                    Vector3 ink = Vector3.LerpUnclamped(bottom, top, ty);
                    left = Math.Min(left, ink.x); right = Math.Max(right, ink.x);
                    if (corner == 0) bottomLeft = ink; if (corner == 1) topLeft = ink;
                }
                chars.Add(new Character { index = i, line = info.lineNumber, text = info.character.ToString(),
                    font = info.fontAsset.name, italic = (info.style & FontStyles.Italic) != 0,
                    origin = info.origin, advance = info.xAdvance, inkLeft = left, inkRight = right,
                    tilt = topLeft.x - bottomLeft.x, quad = quad });
            }
            var boundaries = new List<Boundary>();
            for (int i = 1; i < chars.Count; i++)
                if (chars[i - 1].line == chars[i].line && chars[i - 1].italic != chars[i].italic)
                    boundaries.Add(new Boundary { left = chars[i - 1].index, right = chars[i].index, gap = chars[i].inkLeft - chars[i - 1].inkRight });
            return new Sample { layout = layout, sourceId = SourceIds[sentence], mode = mode, text = clone.text,
                templatePath = PathOf(template.transform), italicStyle = style, fontSize = clone.fontSize,
                width = clone.rectTransform.rect.width, characters = chars.ToArray(), boundaries = boundaries.ToArray() };
        }
        finally { UnityEngine.Object.DestroyImmediate(obj); }
    }

    private static object Read(object obj, string name)
    {
        var property = obj.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (property != null) return property.GetValue(obj, null);
        var field = obj.GetType().GetField(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (field == null) throw new MissingMemberException(obj.GetType().FullName, name);
        return field.GetValue(obj);
    }
    private static float Number(object obj, string name) { return Convert.ToSingle(Read(obj, name)); }
    private static string PathOf(Transform transform)
    {
        string path = transform.name;
        while (transform.parent != null) { transform = transform.parent; path = transform.name + "/" + path; }
        return path;
    }
}
