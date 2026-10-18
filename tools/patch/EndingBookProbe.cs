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
    [Serializable] public class Confirmation
    {
        public string navigation_ending = "END_Delusion", original_sprite, displayed_what, displayed_for, actual_ending_debug;
        public int schema = 1, resource_replay_count, repair_mask_count;
        public float label_size, keyword_size;
        public bool actual_navigation, translated, original, restored, hidden_with_page, no_cover_graphics,
            labels_inside_rows, geometry_fits, styles, resource_replays, burnt_prepared, burnt_original, burnt_restored, passed;
    }
    [Serializable] public class Page
    {
        public string id, what_source, for_source, what_display, for_display, geometry_details;
        public int what_style, for_style;
        public float keyword_size, label_size;
        public bool translated, labels_italic, geometry_fits, labels_inside_rows, keywords_bold, original, restored, sprite_unchanged, turning_occludes_labels,
            burnt_prepared, burnt_original, burnt_restored, burnt_activation_preserved;
    }
    [Serializable] public class Report
    {
        public string input_sha256;
        public bool passed;
        public int page_count;
        public int schema = 2, repair_mask_count;
        public bool no_cover_graphics, source_texture_untouched;
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
    public static IEnumerator CaptureConfirmation(Component canvas, string directory)
    {
        var report = new Confirmation();
        var image = (Image)Field(canvas, "EndingUnlockTexture");
        var page = (Image)Field(canvas, "EndingUnlockPage");
        var what = (TMP_Text)Field(canvas, "EndingTitleWhat");
        var forText = (TMP_Text)Field(canvas, "EndingTitleFor");
        var activeEnding = Field(canvas, "activeEnding");
        object id = activeEnding == null ? null : activeEnding.GetType().GetProperty("Id").GetValue(activeEnding, null);
        report.actual_ending_debug = Convert.ToString(id);
        report.actual_navigation = canvas.gameObject.activeInHierarchy && page.gameObject.activeInHierarchy
            && id != null && id.Equals(Activator.CreateInstance(id.GetType(), new object[] { "END_Delusion" }));
        var layerTransform = what.transform.parent.Find("ElsinoreHanBookLabels");
        // 旧版未拦截GameOverUI.Activate，必须以缺层明确失败，不能只验证普通词表。
        if (layerTransform == null) throw new InvalidOperationException("结局确认页仍缺少图片标题翻译层");
        var layer = layerTransform.gameObject;
        var a = layer.transform.Find("SacrificeText").GetComponent<TMP_Text>();
        var b = layer.transform.Find("forText").GetComponent<TMP_Text>();
        var labels = image.GetComponent("EndingBookLabels");
        var original = (Sprite)labels.GetType().GetProperty("OriginalSprite").GetValue(labels, null);
        var clean = (Sprite)labels.GetType().GetProperty("CleanSprite").GetValue(labels, null);
        var burnt = (Image)Field(canvas, "BurntEndingUnlockOverlay");
        var originalBurnt = (Sprite)labels.GetType().GetProperty("OriginalBurntSprite").GetValue(labels, null);
        var cleanBurnt = (Sprite)labels.GetType().GetProperty("CleanBurntSprite").GetValue(labels, null);
        bool burntActive = burnt.gameObject.activeSelf;
        MonoBehaviour toggle = null;
        foreach (var item in Resources.FindObjectsOfTypeAll<MonoBehaviour>()) if (item != null && item.GetType().Name == "TranslationToggle") toggle = item;
        var handle = toggle.GetType().GetMethod("HandleKey");
        var mode = toggle.GetType().GetMethod("IsTranslatedMode");
        bool initial = (bool)mode.Invoke(toggle, null);
        if (!initial) handle.Invoke(toggle, new object[] { true });
        try
        {
            report.original_sprite = original.name;
            report.repair_mask_count = (int)labels.GetType().GetProperty("RepairMaskCount").GetValue(labels, null);
            report.displayed_what = what.text; report.displayed_for = forText.text;
            report.translated = what.text == "现实" && forText.text == "欢乐" && a.text == "<i>舍弃</i>" && b.text == "<i>换取</i>"
                && layer.activeInHierarchy && image.sprite == clean && original.name == "UI_Book_Unlock";
            report.burnt_prepared = originalBurnt != null && originalBurnt.name == "UI_Book_Unlock_Burnt"
                && cleanBurnt != null && burnt.sprite == cleanBurnt;
            if (!report.burnt_prepared) throw new InvalidOperationException("确认页烧毁叠层未去字");
            report.no_cover_graphics = layer.GetComponentsInChildren<Image>(true).Length == 0 && layer.GetComponentsInChildren<RawImage>(true).Length == 0;
            report.label_size = a.fontSize; report.keyword_size = what.fontSize;
            report.styles = (what.fontStyle & FontStyles.Bold) != 0 && (forText.fontStyle & FontStyles.Bold) != 0
                && a.fontSize == what.fontSize * 0.8f;
            report.geometry_fits = Fits(a) && Fits(b) && Fits(what) && Fits(forText);
            report.styles &= (a.textInfo.characterInfo[0].style & FontStyles.Italic) != 0 && (b.textInfo.characterInfo[0].style & FontStyles.Italic) != 0;
            report.labels_inside_rows = InsideRow(a, image, new Rect(0.15f, 1f - 270f / 1252, 0.75f, 110f / 1252))
                && InsideRow(b, image, new Rect(0.15f, 1f - 490f / 1252, 0.75f, 102f / 1252));
            File.WriteAllBytes(Path.Combine(directory, "confirmation-clean.rgba"), clean.texture.GetRawTextureData());
            EndingBookArtProbe.Dump(canvas, image, directory, "confirmation");
            File.WriteAllBytes(Path.Combine(directory, "confirmation-burnt-clean.rgba"), cleanBurnt.texture.GetRawTextureData());
            try
            {
                // 仅重放可见层，不改已采用结局或任何逻辑标志。
                burnt.gameObject.SetActive(true);
                EndingBookArtProbe.Dump(canvas, image, directory, "confirmation-burnt");
            }
            finally { burnt.gameObject.SetActive(burntActive); }
            handle.Invoke(toggle, new object[] { true });
            yield return new WaitForSecondsRealtime(0.2f);
            report.burnt_original = burnt.sprite == originalBurnt && burnt.gameObject.activeSelf == burntActive;
            report.original = what.text == "REALITY" && forText.text == "JOY" && !layer.activeSelf && image.sprite == original;
            handle.Invoke(toggle, new object[] { true });
            yield return new WaitForSecondsRealtime(0.2f);
            report.burnt_restored = burnt.sprite == cleanBurnt && burnt.gameObject.activeSelf == burntActive;
            report.restored = what.text == "现实" && forText.text == "欢乐" && layer.activeInHierarchy && image.sprite == clean;
            // 在相同真实控件上重放全部来源标题；不篡改activeEnding、解锁或剧情状态。
            report.resource_replays = true;
            foreach (string line in File.ReadAllLines(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BOOK_PAGES"), Encoding.UTF8))
            {
                var parts = line.Split('\t');
                what.text = Decode(parts[2]); forText.text = Decode(parts[4]);
                yield return new WaitForSecondsRealtime(0.1f);
                report.resource_replays &= what.text == Decode(parts[3]) && forText.text == Decode(parts[5]) && Fits(what) && Fits(forText)
                    && a.text == "<i>舍弃</i>" && b.text == "<i>换取</i>" && layer.activeInHierarchy;
                report.resource_replay_count++;
            }
            what.text = "REALITY"; forText.text = "JOY";
            page.gameObject.SetActive(false);
            handle.Invoke(toggle, new object[] { true }); handle.Invoke(toggle, new object[] { true });
            report.hidden_with_page = !layer.activeInHierarchy && image.sprite == original;
            page.gameObject.SetActive(true);
            handle.Invoke(toggle, new object[] { true }); handle.Invoke(toggle, new object[] { true });
            report.hidden_with_page &= layer.activeInHierarchy && image.sprite == clean;
            report.passed = report.actual_navigation && report.translated && report.original && report.restored && report.hidden_with_page
                && report.no_cover_graphics && report.labels_inside_rows && report.geometry_fits && report.styles
                && report.resource_replays && report.resource_replay_count > 0 && report.repair_mask_count > 0
                && report.burnt_prepared && report.burnt_original && report.burnt_restored;
        }
        finally
        {
            page.gameObject.SetActive(true);
            if ((bool)mode.Invoke(toggle, null) != initial) handle.Invoke(toggle, new object[] { true });
            File.WriteAllText(Path.Combine(directory, "ending-confirmation.json"), JsonUtility.ToJson(report, true), new UTF8Encoding(false));
        }
        if (!report.passed) throw new InvalidOperationException("结局确认页图片标题、样式、F8或真实来源重放失败");
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
                var layer = what.transform.parent.Find("ElsinoreHanBookLabels").gameObject;
                var a = layer.transform.Find("SacrificeText").GetComponent<TMP_Text>();
                var b = layer.transform.Find("forText").GetComponent<TMP_Text>();
                var labels = image.GetComponent("EndingBookLabels");
                var original = (Sprite)labels.GetType().GetProperty("OriginalSprite").GetValue(labels, null);
                var clean = (Sprite)labels.GetType().GetProperty("CleanSprite").GetValue(labels, null);
                var burnt = (Image)Field(book, "BurntOverlay");
                var originalBurnt = (Sprite)labels.GetType().GetProperty("OriginalBurntSprite").GetValue(labels, null);
                var cleanBurnt = (Sprite)labels.GetType().GetProperty("CleanBurntSprite").GetValue(labels, null);
                bool burntActive = burnt.gameObject.activeSelf;
                if (originalBurnt == null || cleanBurnt == null) throw new InvalidOperationException("命运书页烧毁叠层未去字");
                report.repair_mask_count = (int)labels.GetType().GetProperty("RepairMaskCount").GetValue(labels, null);
                report.no_cover_graphics = layer.GetComponentsInChildren<Image>(true).Length == 0 && layer.GetComponentsInChildren<RawImage>(true).Length == 0;
                report.source_texture_untouched = original.texture != clean.texture;
                if (index == 0)
                {
                    File.WriteAllBytes(Path.Combine(directory, "paper-source.rgba"), (byte[])labels.GetType().GetMethod("ReadSourcePixels").Invoke(null, null));
                    File.WriteAllBytes(Path.Combine(directory, "paper-clean.rgba"), clean.texture.GetRawTextureData());
                    EndingBookArtProbe.Dump(book, image, directory, "normal");
                    File.WriteAllBytes(Path.Combine(directory, "burnt-clean.rgba"), cleanBurnt.texture.GetRawTextureData());
                    try
                    {
                        burnt.gameObject.SetActive(true);
                        EndingBookArtProbe.Dump(book, image, directory, "burnt");
                    }
                    finally { burnt.gameObject.SetActive(burntActive); }
                }
                var page = new Page { id = expected[0], what_source = whatSource, for_source = forSource,
                    what_display = what.text, for_display = forText.text, what_style = (int)what.fontStyle,
                    for_style = (int)forText.fontStyle, keyword_size = what.fontSize, label_size = a.fontSize };
                page.burnt_prepared = originalBurnt.name == "UI_Book_BurntOverlay" && burnt.sprite == cleanBurnt;
                page.translated = what.text == Decode(expected[3]) && forText.text == Decode(expected[5])
                    && a.text == "<i>舍弃</i>" && b.text == "<i>换取</i>" && layer.activeInHierarchy;
                page.geometry_fits = Fits(a) && Fits(b) && Fits(what) && Fits(forText);
                // 取真实原图分隔线之间的空白行，不把擦除英文的小块区域误作整行。
                page.labels_inside_rows = InsideRow(a, image, new Rect(0.57f, 0.759f, 0.33f, 0.105f))
                    && InsideRow(b, image, new Rect(0.57f, 0.602f, 0.33f, 0.076f));
                page.keywords_bold = (what.fontStyle & FontStyles.Bold) != 0 && (forText.fontStyle & FontStyles.Bold) != 0;
                page.geometry_details = Measure(a) + " | " + Measure(b) + " | " + Measure(what) + " | " + Measure(forText);
                page.labels_italic = a.textInfo.characterCount > 0 && b.textInfo.characterCount > 0
                    && (a.textInfo.characterInfo[0].style & FontStyles.Italic) != 0
                    && (b.textInfo.characterInfo[0].style & FontStyles.Italic) != 0;
                handle.Invoke(toggle, new object[] { true });
                yield return new WaitForSecondsRealtime(0.2f);
                page.burnt_original = burnt.sprite == originalBurnt;
                page.original = what.text == whatSource && forText.text == forSource && !layer.activeSelf
                    && image.sprite == original && (int)what.fontStyle == page.what_style && (int)forText.fontStyle == page.for_style;
                handle.Invoke(toggle, new object[] { true });
                yield return new WaitForSecondsRealtime(0.2f);
                page.burnt_restored = burnt.sprite == cleanBurnt;
                page.burnt_activation_preserved = burnt.gameObject.activeSelf == burntActive;
                page.restored = what.text == page.what_display && forText.text == page.for_display && layer.activeInHierarchy;
                page.sprite_unchanged = image.sprite == clean && (Sprite)labels.GetType().GetProperty("OriginalSprite").GetValue(labels, null) == original;
                object hoverButton = Field(book, index + 1 < endings.Length ? "NextPageButton" : "PrevPageButton");
                ((UnityEngine.Events.UnityEvent)hoverButton.GetType().GetProperty("OnHoverEnterEvt").GetValue(hoverButton, null)).Invoke();
                yield return new WaitForSecondsRealtime(0.2f);
                Canvas.ForceUpdateCanvases();
                var turning = (Image)Field(book, "Background");
                page.turning_occludes_labels = turning.gameObject.activeInHierarchy && turning.depth > a.depth && turning.depth > b.depth
                    && turning.depth > what.depth && turning.depth > forText.depth && a.transform.parent == b.transform.parent
                    && a.transform.IsChildOf(what.transform.parent);
                if (index == 0) EndingBookArtProbe.Dump(book, image, directory, "turn-right");
                if (index + 1 == endings.Length) EndingBookArtProbe.Dump(book, image, directory, "turn-left");
                ((UnityEngine.Events.UnityEvent)hoverButton.GetType().GetProperty("OnHoverExitEvt").GetValue(hoverButton, null)).Invoke();
                yield return new WaitForSecondsRealtime(0.1f);
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
            report.passed = report.page_count == cases.Count && report.no_cover_graphics && report.source_texture_untouched && report.repair_mask_count > 0
                && report.pages.TrueForAll(p => p.translated && p.labels_italic && p.geometry_fits && p.labels_inside_rows && p.keywords_bold && p.original && p.restored && p.sprite_unchanged && p.turning_occludes_labels
                    && p.burnt_prepared && p.burnt_original && p.burnt_restored && p.burnt_activation_preserved);
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
