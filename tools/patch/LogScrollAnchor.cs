using System;
using System.Collections;
using System.Reflection;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// F8 只保持真实对话记录中的阅读段落，不改历史内容或平时的滚动行为。
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
        public int ParagraphIndex;
        public string Outcome = "captured";
        public float RestoreError;
        public int EntryInstanceId { get { return entry == null ? 0 : entry.GetInstanceID(); } }
        public float CapturedY { get { return capturedY; } }

        // 探针读取真实当前段落位置，不能仅由滚动条比例判断是否回到原处。
        public bool TryReadCurrentY(out float y)
        {
            y = 0;
            return entry != null && viewport != null && ParagraphBaseline(entry, viewport, ParagraphIndex, out y);
        }
    }

    public static Anchor Capture()
    {
        int token = ++generation;
        try
        {
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
                    entry.ForceMeshUpdate();
                    TMP_TextInfo info = entry.textInfo;
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
                        int paragraph = ParagraphAt(entry.text, rawIndex);
                        float baseline;
                        if (!ParagraphBaseline(entry, viewport, paragraph, out baseline)) continue;
                        bestDistance = distance;
                        best = new Anchor {
                            log = log, scroll = scroll, viewport = viewport, entry = entry,
                            generation = token, entryIndex = index, entryCount = entries.Count,
                            historySource = history[index], paragraphCount = ParagraphCount(entry.text),
                            ParagraphIndex = paragraph, capturedY = baseline
                        };
                    }
                }
                return best;
            }
        }
        catch { /* 阅读位置保护不能阻断 F8 或原游戏。 */ }
        return null;
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
            IList entries = ReadField(anchor.log, "createdEntries") as IList;
            string[] history = ReadHistory(anchor.log);
            if (entries == null || history == null || entries.Count != anchor.entryCount
                || history.Length != anchor.entryCount || !ReferenceEquals(entries[anchor.entryIndex], anchor.entry)
                || !String.Equals(history[anchor.entryIndex], anchor.historySource, StringComparison.Ordinal))
            { anchor.Outcome = "history-changed"; return false; }
            // 中英文硬换行结构不一致时没有可靠的段落对应，不按高度比例猜测。
            if (ParagraphCount(anchor.entry.text) != anchor.paragraphCount)
            { anchor.Outcome = "paragraphs-changed"; return false; }
            Canvas.ForceUpdateCanvases();
            for (int index = 0; index < entries.Count; index++)
            {
                TMP_Text entry = entries[index] as TMP_Text;
                if (entry != null && entry.gameObject.activeInHierarchy) entry.ForceMeshUpdate();
            }
            LayoutRebuilder.ForceRebuildLayoutImmediate(anchor.scroll.content);
            Canvas.ForceUpdateCanvases();
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

    private static bool ParagraphBaseline(TMP_Text entry, RectTransform viewport, int paragraph, out float baseline)
    {
        baseline = 0;
        int start = ParagraphStart(entry.text, paragraph);
        if (start < 0) return false;
        TMP_TextInfo info = entry.textInfo;
        for (int index = 0; index < info.characterCount; index++)
        {
            TMP_CharacterInfo character = info.characterInfo[index];
            if (character.index < start || character.character == '\r' || character.character == '\n') continue;
            if (ParagraphAt(entry.text, character.index) != paragraph) return false;
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
