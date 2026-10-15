using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 通过真实翻页按钮消费全部书页；不解锁结局、不选择重温，也不修改结局元数据。
public static class EndingBookProbe
{
    [Serializable] public class Page
    {
        public string id, what_source, for_source, what_display, for_display, geometry_details;
        public int what_style, for_style;
        public float keyword_size, label_size;
        public bool translated, labels_italic, geometry_fits, labels_inside_rows, keywords_bold, original, restored, sprite_unchanged;
    }
    [Serializable] public class Report
    {
        public string input_sha256;
        public bool passed;
        public int page_count;
        public List<Page> pages = new List<Page>();
    }
    private const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static object Field(object value, string key) { return value.GetType().GetField(key, flags).GetValue(value); }
    private static string Prop(object value, string key) { return (string)value.GetType().GetProperty(key).GetValue(value, null); }
    private static string Decode(string value) { return Encoding.UTF8.GetString(Convert.FromBase64String(value)); }
    private static bool Fits(TMP_Text text)
    {
        text.ForceMeshUpdate();
        if (text.isTextOverflowing || text.textInfo.lineCount != 1) return false;
        foreach (char character in text.GetParsedText())
            if (!Char.IsWhiteSpace(character) && !text.font.HasCharacter(character, true)) return false;
        return true;
    }
    private static string Measure(TMP_Text text)
    {
        var result = new StringBuilder(text.name + ":rect=" + text.rectTransform.rect + ";preferred=" + text.preferredWidth + "," + text.preferredHeight
            + ";bounds=" + text.textBounds + ";local=" + text.transform.localPosition
            + ";overflow=" + text.isTextOverflowing + ";lines=" + text.textInfo.lineCount + ";font=" + text.font.name + ";missing=");
        foreach (char character in text.GetParsedText())
            if (!Char.IsWhiteSpace(character) && !text.font.HasCharacter(character, true)) result.Append(((int)character).ToString("X4") + ",");
        return result.ToString();
    }
    private static bool InsideRow(TMP_Text text, Image book, Rect row)
    {
        // textBounds包含字体上下行度量；判断分隔线重叠须用可见字符的真实网格四角。
        Rect page = book.rectTransform.rect;
        for (int index = 0; index < text.textInfo.characterCount; index++)
        {
            var character = text.textInfo.characterInfo[index];
            if (!character.isVisible) continue;
            foreach (var point in new Vector3[] { character.bottomLeft, character.bottomRight, character.topLeft, character.topRight })
            {
                Vector3 local = book.rectTransform.InverseTransformPoint(text.transform.TransformPoint(point));
                var normalized = new Vector2((local.x - page.x) / page.width, (local.y - page.y) / page.height);
                if (!row.Contains(normalized)) return false;
            }
        }
        return true;
    }
    public static IEnumerator Capture(Component book, string directory)
    {
        string path = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BOOK_PAGES");
        var cases = new Dictionary<string, string[]>();
        foreach (string line in File.ReadAllLines(path, Encoding.UTF8))
        {
            var parts = line.Split('\t');
            if (parts[1] == "True") cases.Add(Decode(parts[2]) + "\n" + Decode(parts[4]), parts);
        }
        var report = new Report();
        using (var sha = SHA256.Create()) report.input_sha256 = BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
        var endings = (Array)Field(book, "UnlockedEndings");
        if (endings.Length != cases.Count || (int)Field(book, "CurrentPage") != 0) throw new InvalidOperationException("真实书页数量或初始页与资源不符");
        MonoBehaviour toggle = null;
        foreach (var item in Resources.FindObjectsOfTypeAll<MonoBehaviour>()) if (item != null && item.GetType().Name == "TranslationToggle") toggle = item;
        var handle = toggle.GetType().GetMethod("HandleKey");
        var mode = toggle.GetType().GetMethod("IsTranslatedMode");
        bool initial = (bool)mode.Invoke(toggle, null);
        if (!initial) handle.Invoke(toggle, new object[] { true });
        try
        {
            for (int index = 0; index < endings.Length; index++)
            {
                var ending = endings.GetValue(index);
                string whatSource = Prop(ending, "SacrificeWhat"), forSource = Prop(ending, "SacrificeFor");
                string[] expected = cases[whatSource + "\n" + forSource];
                var what = (TMP_Text)Field(book, "sacrificeWhatText");
                var forText = (TMP_Text)Field(book, "sacrificeForText");
                var image = (Image)Field(book, "book");
                var layer = image.transform.Find("ElsinoreHanBookLabels").gameObject;
                var a = layer.transform.Find("SacrificeCover/SacrificeText").GetComponent<TMP_Text>();
                var b = layer.transform.Find("forCover/forText").GetComponent<TMP_Text>();
                int sprite = image.sprite.GetInstanceID();
                var page = new Page { id = expected[0], what_source = whatSource, for_source = forSource,
                    what_display = what.text, for_display = forText.text, what_style = (int)what.fontStyle,
                    for_style = (int)forText.fontStyle, keyword_size = what.fontSize, label_size = a.fontSize };
                page.translated = what.text == Decode(expected[3]) && forText.text == Decode(expected[5])
                    && a.text == "<i>舍弃</i>" && b.text == "<i>换取</i>" && layer.activeInHierarchy;
                page.geometry_fits = Fits(a) && Fits(b) && Fits(what) && Fits(forText);
                // 取真实原图分隔线之间的空白行，不把擦除英文的小块区域误作整行。
                page.labels_inside_rows = InsideRow(a, image, new Rect(0.57f, 0.789f, 0.33f, 0.12f))
                    && InsideRow(b, image, new Rect(0.57f, 0.622f, 0.33f, 0.081f));
                page.keywords_bold = (what.fontStyle & FontStyles.Bold) != 0 && (forText.fontStyle & FontStyles.Bold) != 0;
                page.geometry_details = Measure(a) + " | " + Measure(b) + " | " + Measure(what) + " | " + Measure(forText);
                page.labels_italic = a.textInfo.characterCount > 0 && b.textInfo.characterCount > 0
                    && (a.textInfo.characterInfo[0].style & FontStyles.Italic) != 0
                    && (b.textInfo.characterInfo[0].style & FontStyles.Italic) != 0;
                handle.Invoke(toggle, new object[] { true });
                yield return new WaitForSecondsRealtime(0.2f);
                page.original = what.text == whatSource && forText.text == forSource && !layer.activeSelf
                    && (int)what.fontStyle == page.what_style && (int)forText.fontStyle == page.for_style;
                handle.Invoke(toggle, new object[] { true });
                yield return new WaitForSecondsRealtime(0.2f);
                page.restored = what.text == page.what_display && forText.text == page.for_display && layer.activeInHierarchy;
                page.sprite_unchanged = image.sprite.GetInstanceID() == sprite;
                report.pages.Add(page);
                if (index + 1 < endings.Length)
                {
                    object button = Field(book, "NextPageButton");
                    ((Button.ButtonClickedEvent)button.GetType().GetProperty("OnClick").GetValue(button, null)).Invoke();
                    yield return new WaitForSecondsRealtime(0.3f);
                    if ((int)Field(book, "CurrentPage") != index + 1) throw new InvalidOperationException("真实翻页按钮未生效");
                }
            }
            report.page_count = report.pages.Count;
            report.passed = report.page_count == cases.Count && report.pages.TrueForAll(p => p.translated && p.labels_italic && p.geometry_fits && p.labels_inside_rows && p.keywords_bold && p.original && p.restored && p.sprite_unchanged);
        }
        finally
        {
            if ((bool)mode.Invoke(toggle, null) != initial) handle.Invoke(toggle, new object[] { true });
            // 本游戏JsonUtility会漏掉探针嵌套列表，逐页显式序列化后再组装。
            string header = JsonUtility.ToJson(report);
            string[] pages = report.pages.ConvertAll(p => JsonUtility.ToJson(p)).ToArray();
            string json = header.Substring(0, header.Length - 1) + ",\"pages\":[" + String.Join(",", pages) + "]}";
            File.WriteAllText(Path.Combine(directory, "ending-book.json"), json, new UTF8Encoding(false));
        }
        if (!report.passed) throw new InvalidOperationException("命运之书标题、样式、排版或F8回归失败");
    }
}
