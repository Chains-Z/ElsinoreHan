using System;
using System.Collections;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// F8保持真实对话记录、文档或人物介绍的阅读段落，不改正文或平时的滚动行为。
public static class LogScrollAnchor
{
    private const BindingFlags Fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static int generation;
    public static Anchor LastCompleted;

    public sealed class Anchor
    {
        internal Component log;
        internal ScrollRect scroll;
        internal RectTransform viewport;
        internal TMP_Text entry;
        internal int generation;
        internal int entryIndex;
        internal int entryCount;
        internal string historySource;
        internal int paragraphCount;
        internal float capturedY;
        internal bool document;
        internal bool biography;
        internal object portrait;
        public int ParagraphIndex;
        public bool PinnedToBottom;
        public string Outcome = "captured";
        public float RestoreError;
        public int EntryInstanceId { get { return entry == null ? 0 : entry.GetInstanceID(); } }
        public float CapturedY { get { return capturedY; } }
        public bool IsDocument { get { return document; } }
        public bool IsBiography { get { return biography; } }

        // 探针读取真实当前段落位置，不能仅由滚动条比例判断是否回到原处。
        public bool TryReadCurrentY(out float y)
        {
            y = 0;
            return entry != null && viewport != null && ParagraphBaseline(entry, viewport, ParagraphIndex, document, out y);
        }
    }

    public static Anchor Capture()
    {
        int token = ++generation;
        try
        {
            // 文档是模态阅读页；优先于背后可能仍然激活的日志控件。
            Type documentType = FindType("Elsinore.Ui.ObjectCloseupUI");
            if (documentType != null)
            {
                foreach (UnityEngine.Object value in Resources.FindObjectsOfTypeAll(documentType))
                {
                    Component owner = value as Component;
                    if (owner == null || !owner.gameObject.activeInHierarchy || !System.Object.Equals(ReadField(owner, "isOpen"), true)) continue;
                    TMP_Text body = ReadField(owner, "Body") as TMP_Text;
                    StringBuilder builder = ReadField(owner, "builder") as StringBuilder;
                    ScrollRect scroll = body == null ? null : body.GetComponentInParent<ScrollRect>();
                    if (scroll == null || scroll.content == null || builder == null || !body.gameObject.activeInHierarchy
                        || scroll.content != body.rectTransform || scroll.verticalScrollbar != ReadField(owner, "Scrollbar") as Scrollbar) return null;
                    RectTransform viewport = scroll.viewport == null ? scroll.transform as RectTransform : scroll.viewport;
                    if (viewport == null) continue;
                    Canvas.ForceUpdateCanvases();
                    Anchor anchor = CaptureEntry(owner, scroll, viewport, body, token, 0, 1, builder.ToString(), true);
                    // 打开的模态文档没有有效锚点时，不去挪动背后的日志。
                    return anchor;
                }
            }
            Type biographyType = FindType("Elsinore.Ui.JournalCharactersTab");
            if (biographyType != null)
            {
                foreach (UnityEngine.Object value in Resources.FindObjectsOfTypeAll(biographyType))
                {
                    Component owner = value as Component;
                    if (owner == null || !owner.gameObject.activeInHierarchy) continue;
                    TMP_Text body = ReadField(owner, "DescriptionText") as TMP_Text;
                    StringBuilder builder = ReadField(owner, "builder") as StringBuilder;
                    ScrollRect scroll = body == null ? null : body.GetComponentInParent<ScrollRect>();
                    if (body == null || builder == null || scroll == null || scroll.content != body.rectTransform
                        || !body.gameObject.activeInHierarchy) return null;
                    RectTransform viewport = scroll.viewport == null ? scroll.transform as RectTransform : scroll.viewport;
                    Canvas.ForceUpdateCanvases();
                    Anchor anchor = CaptureEntry(owner, scroll, viewport, body, token, 0, 1, builder.ToString(), true);
                    if (anchor != null)
                    {
                        anchor.biography = true;
                        anchor.portrait = ReadField(owner, "HighlightedPortrait");
                        anchor.PinnedToBottom = ShouldPinToBottom(scroll.verticalNormalizedPosition,
                            scroll.content.rect.height - viewport.rect.height);
                    }
                    return anchor;
                }
            }
            Type logType = null;
            foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                logType = assembly.GetType("Elsinore.Ui.LogUI", false);
                if (logType != null) break;
            }
            if (logType == null) return null;
            foreach (UnityEngine.Object value in Resources.FindObjectsOfTypeAll(logType))
            {
                Component log = value as Component;
                if (log == null || !log.gameObject.activeInHierarchy) continue;
                ScrollRect scroll = ReadField(log, "ScrollArea") as ScrollRect;
                IList entries = ReadField(log, "createdEntries") as IList;
                string[] history = ReadHistory(log);
                if (scroll == null || scroll.content == null || entries == null || history == null
                    || history.Length != entries.Count) continue;
                RectTransform viewport = scroll.viewport == null ? scroll.transform as RectTransform : scroll.viewport;
                if (viewport == null) continue;
                Canvas.ForceUpdateCanvases();
                Anchor best = null;
                float bestDistance = float.MaxValue;
                for (int index = 0; index < entries.Count; index++)
                {
                    TMP_Text entry = entries[index] as TMP_Text;
                    if (entry == null || !entry.gameObject.activeInHierarchy) continue;
                    float distance;
                    Anchor candidate = CaptureEntry(log, scroll, viewport, entry, token, index, entries.Count,
                                                    history[index], false, out distance);
                    if (candidate != null && distance < bestDistance)
                    { bestDistance = distance; best = candidate; }
                }
                return best;
            }
        }
        catch { /* 阅读位置保护不能阻断 F8 或原游戏。 */ }
        return null;
    }

    private static Type FindType(string name)
    {
        foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            Type type = assembly.GetType(name, false);
            if (type != null) return type;
        }
        return null;
    }

    private static Anchor CaptureEntry(Component owner, ScrollRect scroll, RectTransform viewport, TMP_Text entry,
                                       int token, int index, int count, string source, bool document)
    {
        float distance;
        return CaptureEntry(owner, scroll, viewport, entry, token, index, count, source, document, out distance);
    }

    private static Anchor CaptureEntry(Component owner, ScrollRect scroll, RectTransform viewport, TMP_Text entry,
                                       int token, int index, int count, string source, bool document, out float bestDistance)
    {
        entry.ForceMeshUpdate();
        TMP_TextInfo info = entry.textInfo;
        Anchor best = null;
        bestDistance = float.MaxValue;
        for (int lineIndex = 0; lineIndex < info.lineCount; lineIndex++)
        {
            TMP_LineInfo line = info.lineInfo[lineIndex];
            if (line.visibleCharacterCount == 0 || line.firstCharacterIndex < 0
                || line.firstCharacterIndex >= info.characterCount) continue;
            float top = LocalY(entry, viewport, line.ascender);
            float bottom = LocalY(entry, viewport, line.descender);
            if (bottom >= viewport.rect.yMax || top <= viewport.rect.yMin) continue;
            float distance = Mathf.Abs(viewport.rect.yMax - Mathf.Min(top, viewport.rect.yMax));
            if (distance >= bestDistance) continue;
            int rawIndex = info.characterInfo[line.firstCharacterIndex].index;
            int paragraph = document ? DocumentParagraphAt(entry.text, rawIndex) : ParagraphAt(entry.text, rawIndex);
            float baseline;
            if (!ParagraphBaseline(entry, viewport, paragraph, document, out baseline)) continue;
            bestDistance = distance;
            best = new Anchor {
                log = owner, scroll = scroll, viewport = viewport, entry = entry, document = document,
                generation = token, entryIndex = index, entryCount = count, historySource = source,
                paragraphCount = document ? DocumentParagraphCount(entry.text) : ParagraphCount(entry.text),
                ParagraphIndex = paragraph, capturedY = baseline,
                PinnedToBottom = !document && ShouldPinToBottom(scroll.verticalNormalizedPosition,
                    scroll.content.rect.height - viewport.rect.height)
            };
        }
        return best;
    }

    public static IEnumerator Restore(Anchor anchor)
    {
        if (anchor == null) yield break;
        // 等待文本切换与 TMP 布局；只做两次有限校正，不持续锁住用户滚动。
        yield return null;
        if (!RestoreOnce(anchor)) yield break;
        yield return null;
        RestoreOnce(anchor);
        LastCompleted = anchor;
    }

    private static bool RestoreOnce(Anchor anchor)
    {
        try
        {
            if (anchor.generation != generation) { anchor.Outcome = "superseded"; return false; }
            if (anchor.log == null || !anchor.log.gameObject.activeInHierarchy || anchor.entry == null
                || !anchor.entry.gameObject.activeInHierarchy || anchor.scroll == null || anchor.viewport == null)
            { anchor.Outcome = "closed"; return false; }
            IList entries = null;
            if (anchor.biography)
            {
                StringBuilder builder = ReadField(anchor.log, "builder") as StringBuilder;
                if (!ReferenceEquals(ReadField(anchor.log, "DescriptionText"), anchor.entry) || builder == null
                    || anchor.scroll.content != anchor.entry.rectTransform
                    || !ReferenceEquals(ReadField(anchor.log, "HighlightedPortrait"), anchor.portrait)
                    || !String.Equals(builder.ToString(), anchor.historySource, StringComparison.Ordinal))
                { anchor.Outcome = "biography-changed"; return false; }
            }
            else if (anchor.document)
            {
                StringBuilder builder = ReadField(anchor.log, "builder") as StringBuilder;
                if (!System.Object.Equals(ReadField(anchor.log, "isOpen"), true))
                { anchor.Outcome = "closed"; return false; }
                if (!ReferenceEquals(ReadField(anchor.log, "Body"), anchor.entry) || builder == null
                    || anchor.scroll.content != anchor.entry.rectTransform
                    || anchor.scroll.verticalScrollbar != ReadField(anchor.log, "Scrollbar") as Scrollbar
                    || !String.Equals(builder.ToString(), anchor.historySource, StringComparison.Ordinal))
                { anchor.Outcome = "document-changed"; return false; }
            }
            else
            {
                entries = ReadField(anchor.log, "createdEntries") as IList;
                string[] history = ReadHistory(anchor.log);
                if (entries == null || history == null || entries.Count != anchor.entryCount
                    || history.Length != anchor.entryCount || !ReferenceEquals(entries[anchor.entryIndex], anchor.entry)
                    || !String.Equals(history[anchor.entryIndex], anchor.historySource, StringComparison.Ordinal))
                { anchor.Outcome = "history-changed"; return false; }
            }
            // 中英文硬换行结构不一致时没有可靠的段落对应，不按高度比例猜测。
            int currentCount = anchor.document ? DocumentParagraphCount(anchor.entry.text) : ParagraphCount(anchor.entry.text);
            if (currentCount != anchor.paragraphCount && !anchor.PinnedToBottom)
            { anchor.Outcome = "paragraphs-changed"; return false; }
            Canvas.ForceUpdateCanvases();
            if (anchor.document) anchor.entry.ForceMeshUpdate();
            else for (int index = 0; index < entries.Count; index++)
            {
                TMP_Text entry = entries[index] as TMP_Text;
                if (entry != null && entry.gameObject.activeInHierarchy) entry.ForceMeshUpdate();
            }
            LayoutRebuilder.ForceRebuildLayoutImmediate(anchor.scroll.content);
            Canvas.ForceUpdateCanvases();
            // 已读到底部时，切换后继续展示末尾；保留上沿段落会把较长的英文尾部挤出视口。
            // 每次F8重新捕获，手动滚离底部后仍走原来的段落定位，不能持续吸附末尾。
            if (anchor.PinnedToBottom)
            {
                anchor.scroll.StopMovement();
                anchor.scroll.verticalNormalizedPosition = 0;
                Canvas.ForceUpdateCanvases();
                float hidden = Mathf.Max(0, anchor.scroll.content.rect.height - anchor.viewport.rect.height);
                anchor.RestoreError = Mathf.Abs(anchor.scroll.verticalNormalizedPosition) * hidden;
                anchor.Outcome = anchor.RestoreError <= 1f ? "bottom-restored" : "bottom-unavailable";
                LastCompleted = anchor;
                return anchor.RestoreError <= 1f;
            }
            float y;
            if (!anchor.TryReadCurrentY(out y)) { anchor.Outcome = "missing-paragraph"; return false; }
            anchor.scroll.StopMovement();
            Vector3 worldDelta = anchor.viewport.TransformVector(new Vector3(0, anchor.capturedY - y, 0));
            Vector3 localDelta = anchor.scroll.content.parent.InverseTransformVector(worldDelta);
            anchor.scroll.content.anchoredPosition += new Vector2(localDelta.x, localDelta.y);
            // 首尾无法维持任意屏幕高度时保持合法边界，避免把内容拖出视口。
            anchor.scroll.verticalNormalizedPosition = Mathf.Clamp01(anchor.scroll.verticalNormalizedPosition);
            Canvas.ForceUpdateCanvases();
            if (!anchor.TryReadCurrentY(out y)) { anchor.Outcome = "missing-paragraph"; return false; }
            anchor.RestoreError = Mathf.Abs(y - anchor.capturedY);
            anchor.Outcome = anchor.RestoreError <= 1f ? "restored" : "boundary-clamped";
            LastCompleted = anchor;
            return true;
        }
        catch { anchor.Outcome = "unavailable"; LastCompleted = anchor; return false; }
    }

    private static object ReadField(object value, string name)
    {
        FieldInfo field = value.GetType().GetField(name, Fields);
        return field == null ? null : field.GetValue(value);
    }

    // 使用实际内容距离判断，避免长日志中的固定比例阈值误吞几十行用户滚动。
    public static bool ShouldPinToBottom(float normalizedPosition, float hiddenHeight)
    {
        return !Single.IsNaN(normalizedPosition) && !Single.IsInfinity(normalizedPosition)
            && !Single.IsNaN(hiddenHeight) && !Single.IsInfinity(hiddenHeight)
            && hiddenHeight > 1f && Mathf.Abs(normalizedPosition) * hiddenHeight <= 1f;
    }

    private static string[] ReadHistory(Component log)
    {
        object tracker = ReadField(log, "ht");
        if (tracker == null) return null;
        PropertyInfo property = tracker.GetType().GetProperty("HistoryText", Fields);
        return property == null ? null : property.GetValue(tracker, null) as string[];
    }

    public static int ParagraphCount(string text)
    {
        return ParagraphAt(text, text == null ? 0 : text.Length) + 1;
    }

    public static int ParagraphAt(string text, int rawIndex)
    {
        if (text == null) return 0;
        int paragraph = 0;
        for (int index = 0; index < Math.Min(Math.Max(rawIndex, 0), text.Length); index++)
            if (text[index] == '\n') paragraph++;
        return paragraph;
    }

    public static int ParagraphStart(string text, int paragraph)
    {
        if (text == null || paragraph < 0) return -1;
        if (paragraph == 0) return 0;
        for (int index = 0; index < text.Length; index++)
            if (text[index] == '\n' && --paragraph == 0) return index + 1;
        return -1;
    }

    // 文档的空白分隔数量可能因翻译不同；只对应非空硬行，不改原正文。
    public static int DocumentParagraphCount(string text)
    {
        if (text == null) return 0;
        int count = 0;
        int start = 0;
        while (start <= text.Length)
        {
            int end = text.IndexOf('\n', start);
            if (end < 0) end = text.Length;
            if (HasParagraphContent(text, start, end)) count++;
            if (end == text.Length) break;
            start = end + 1;
        }
        return count;
    }

    public static int DocumentParagraphAt(string text, int rawIndex)
    {
        if (text == null) return 0;
        int paragraph = 0, ordinal = 0, start = 0;
        while (start <= text.Length && start <= rawIndex)
        {
            int end = text.IndexOf('\n', start);
            if (end < 0) end = text.Length;
            if (HasParagraphContent(text, start, end)) paragraph = ordinal++;
            if (end == text.Length) break;
            start = end + 1;
        }
        return paragraph;
    }

    public static int DocumentParagraphStart(string text, int paragraph)
    {
        if (text == null || paragraph < 0) return -1;
        int ordinal = 0, start = 0;
        while (start <= text.Length)
        {
            int end = text.IndexOf('\n', start);
            if (end < 0) end = text.Length;
            if (HasParagraphContent(text, start, end) && ordinal++ == paragraph) return start;
            if (end == text.Length) break;
            start = end + 1;
        }
        return -1;
    }

    private static bool HasParagraphContent(string text, int start, int end)
    {
        bool tag = false;
        for (int index = start; index < end; index++)
        {
            if (text[index] == '<') tag = true;
            else if (text[index] == '>') tag = false;
            else if (!tag && !Char.IsWhiteSpace(text[index])) return true;
        }
        return false;
    }

    private static bool ParagraphBaseline(TMP_Text entry, RectTransform viewport, int paragraph, bool document, out float baseline)
    {
        baseline = 0;
        int start = document ? DocumentParagraphStart(entry.text, paragraph) : ParagraphStart(entry.text, paragraph);
        if (start < 0) return false;
        TMP_TextInfo info = entry.textInfo;
        for (int index = 0; index < info.characterCount; index++)
        {
            TMP_CharacterInfo character = info.characterInfo[index];
            if (character.index < start || character.character == '\r' || character.character == '\n') continue;
            if ((document ? DocumentParagraphAt(entry.text, character.index) : ParagraphAt(entry.text, character.index)) != paragraph) return false;
            baseline = LocalY(entry, viewport, info.lineInfo[character.lineNumber].baseline);
            return true;
        }
        return false;
    }

    private static float LocalY(TMP_Text entry, RectTransform viewport, float y)
    {
        return viewport.InverseTransformPoint(entry.transform.TransformPoint(new Vector3(0, y, 0))).y;
    }
}
