using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 只在真实 LogUI 已打开的隔离探针内运行，不生成历史或修改历史文本。
public static class LogScrollAnchorProbe
{
    private const BindingFlags Members = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
    private sealed class Context
    {
        public Component Log;
        public ScrollRect Scroll;
        public MonoBehaviour Toggle;
        public Type Helper;
        public bool InitialMode;
        public Vector2 InitialPosition;
        public float Deadline;
        public bool Complete;
        public bool InitialCaptured;
        public string Path;
        public StringBuilder Report = new StringBuilder();
        public void Line(string value) { Report.AppendLine(value); File.WriteAllText(Path, Report.ToString(), new UTF8Encoding(false)); }
    }

    public static IEnumerator Capture(Component log, string outputDirectory)
    {
        var context = new Context { Log = log, Path = System.IO.Path.Combine(outputDirectory, "log-scroll-anchor.tsv"), Deadline = Time.realtimeSinceStartup + 15f };
        context.Line("SCHEMA\t1");
        context.Line("SCOPE\t" + Enc("真实冻结历史控件、TMP基线与正式F8共享路径；坐标为UI单位，非物理键盘或像素验收"));
        var routines = new Stack<IEnumerator>();
        routines.Push(Core(context));
        try
        {
            while (routines.Count > 0)
            {
                bool more = false;
                object current = null;
                Exception failure = null;
                try
                {
                    if (Time.realtimeSinceStartup > context.Deadline) throw new TimeoutException("日志阅读位置诊断超过15秒");
                    more = routines.Peek().MoveNext();
                    if (more) current = routines.Peek().Current;
                }
                catch (Exception error) { failure = error; }
                if (failure != null) { context.Line("FAILURE\t" + Enc(failure.ToString())); break; }
                if (!more) { routines.Pop(); continue; }
                IEnumerator child = current as IEnumerator;
                if (child != null) { routines.Push(child); continue; }
                yield return current;
            }
        }
        finally
        {
            try
            {
                if (context.Toggle != null && context.InitialCaptured) SetMode(context, context.InitialMode);
                // 取消故障路径可能仍待执行的两帧恢复，再还原诊断前的滚动坐标。
                if (context.Helper != null) context.Helper.GetMethod("Capture").Invoke(null, null);
                if (context.Scroll != null) { context.Scroll.StopMovement(); context.Scroll.content.anchoredPosition = context.InitialPosition; }
            }
            catch (Exception error) { context.Complete = false; context.Line("FAILURE\t" + Enc("清理失败：" + error)); }
            context.Line("STATUS\t" + (context.Complete ? "COLLECTED" : "FAILED"));
        }
    }

    private static IEnumerator Core(Context context)
    {
        if (!Application.isBatchMode || string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH")))
            throw new InvalidOperationException("日志诊断需要既有后台隔离保护");
        bool saveGuard = false, inputGuard = false;
        foreach (MonoBehaviour component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
        {
            if (component == null) continue;
            if (component.GetType().Name == "TranslationToggle") context.Toggle = component;
            if (component.GetType().Name == "RuntimeProbe")
            {
                saveGuard = (bool)Field(component, "saveGuardActive");
                inputGuard = (bool)component.GetType().GetField("physicalInputGuardActive", BindingFlags.NonPublic | BindingFlags.Static).GetValue(null);
            }
        }
        context.Line("SAVE_GUARD_ACTIVE\t" + saveGuard);
        context.Line("PHYSICAL_INPUT_GUARD_ACTIVE\t" + inputGuard);
        if (!saveGuard || !inputGuard || context.Toggle == null) throw new InvalidOperationException("真实隔离/F8保护不完整");
        if (context.Log == null || context.Log.GetType().FullName != "Elsinore.Ui.LogUI" || !context.Log.gameObject.activeInHierarchy)
            throw new InvalidOperationException("当前真实LogUI未打开");
        context.Scroll = Field(context.Log, "ScrollArea") as ScrollRect;
        context.Helper = context.Toggle.GetType().Assembly.GetType("LogScrollAnchor", true);
        context.InitialMode = Mode(context);
        context.InitialPosition = context.Scroll.content.anchoredPosition;
        context.InitialCaptured = true;
        context.Line("NAVIGATION\tlog\tTrue\tTrue");
        SetMode(context, true);
        for (int frame = 0; frame < 4; frame++) yield return null;
        string[] history = History(context);
        IList entries = Field(context.Log, "createdEntries") as IList;
        if (history == null || entries == null || history.Length != entries.Count) throw new InvalidOperationException("真实日志历史与控件绑定不一致");
        context.Line("HISTORY_COUNT\t" + history.Length);
        int shortest = -1, longest = -1;
        for (int index = 0; index < history.Length; index++)
        {
            TMP_Text text = entries[index] as TMP_Text;
            if (text == null || !text.gameObject.activeInHierarchy) throw new InvalidOperationException("日志控件失活");
            text.ForceMeshUpdate();
            context.Line("HISTORY\t" + index + "\t" + text.GetInstanceID() + "\t" + Enc(history[index]));
            if (String.IsNullOrEmpty(history[index]) || text.textInfo.lineCount == 0) continue;
            if (shortest < 0 || history[index].Length < history[shortest].Length) shortest = index;
            if (longest < 0 || history[index].Length > history[longest].Length) longest = index;
        }
        if (shortest < 0 || longest < 0 || shortest == longest)
        { context.Line("UNAVAILABLE\thistory-diversity\t" + Enc("真实历史没有长短两种非空条目")); yield break; }
        context.Scroll.StopMovement();
        context.Scroll.verticalNormalizedPosition = 0.5f;
        for (int frame = 0; frame < 3; frame++) yield return null;
        yield return Case(context, "middle", -1, "middle");
        string[] names = { "short", "long-upper", "long-lower" };
        int[] indices = { shortest, longest, longest };
        float[] portions = { 0.5f, 0.25f, 0.75f };
        for (int sample = 0; sample < names.Length; sample++)
        {
            TMP_Text text = entries[indices[sample]] as TMP_Text;
            text.ForceMeshUpdate();
            int lineIndex = Math.Min(text.textInfo.lineCount - 1, (int)(text.textInfo.lineCount * portions[sample]));
            RectTransform viewport = context.Scroll.viewport == null ? context.Scroll.transform as RectTransform : context.Scroll.viewport;
            float currentY = viewport.InverseTransformPoint(text.transform.TransformPoint(new Vector3(0, text.textInfo.lineInfo[lineIndex].baseline, 0))).y;
            Vector3 delta = context.Scroll.content.parent.InverseTransformVector(viewport.TransformVector(new Vector3(0, viewport.rect.yMax - 12f - currentY, 0)));
            context.Scroll.content.anchoredPosition += new Vector2(delta.x, delta.y);
            context.Scroll.verticalNormalizedPosition = Mathf.Clamp01(context.Scroll.verticalNormalizedPosition);
            for (int frame = 0; frame < 3; frame++) yield return null;
            yield return Case(context, names[sample], indices[sample], sample == 0 ? "short" : "long");
        }
        SetMode(context, context.InitialMode);
        for (int frame = 0; frame < 4; frame++) yield return null;
        context.Complete = true;
    }

    private static IEnumerator Case(Context context, string name, int intendedIndex, string kind)
    {
        context.Line("CASE\t" + name + "\t" + intendedIndex + "\t" + kind);
        SetMode(context, true);
        for (int frame = 0; frame < 4; frame++) yield return null;
        for (int leg = 0; leg < 2; leg++)
        {
            string mode = leg == 0 ? "original" : "restored";
            object before = context.Helper.GetMethod("Capture").Invoke(null, null);
            if (before == null) { context.Line("UNAVAILABLE\t" + name + "\t" + Enc("真实视口没有可采集的TMP网格锚点")); yield break; }
            int index = (int)Field(before, "entryIndex");
            if (intendedIndex >= 0 && index != intendedIndex)
            { context.Line("UNAVAILABLE\t" + name + "\t" + Enc("布局边界无法让目标真实条目成为当前阅读锚点")); yield break; }
            Snapshot(context, name, mode, "before", before);
            SetMode(context, leg != 0);
            for (int frame = 0; frame < 4; frame++) yield return null;
            object after = context.Helper.GetField("LastCompleted").GetValue(null);
            if (after == null) { context.Line("UNAVAILABLE\t" + name + "\t" + Enc("正式F8路径没有恢复完成证据")); yield break; }
            Snapshot(context, name, mode, "after", after);
        }
    }

    private static void Snapshot(Context context, string name, string mode, string stage, object anchor)
    {
        TMP_Text entry = Field(anchor, "entry") as TMP_Text;
        object[] coordinates = { 0f };
        bool read = (bool)anchor.GetType().GetMethod("TryReadCurrentY").Invoke(anchor, coordinates);
        int index = (int)Field(anchor, "entryIndex");
        context.Line("SAMPLE\t" + name + "\t" + mode + "\t" + stage + "\t" + index + "\t" + Property(anchor, "EntryInstanceId")
            + "\t" + Field(anchor, "ParagraphIndex") + "\t" + Number((float)Property(anchor, "CapturedY"))
            + "\t" + read + "\t" + Number((float)coordinates[0]) + "\t" + Field(anchor, "Outcome")
            + "\t" + Number((float)Field(anchor, "RestoreError")) + "\t" + Mode(context)
            + "\t" + (entry != null && entry.gameObject.activeInHierarchy) + "\t" + Enc(History(context)[index])
            + "\t" + Enc(entry == null ? "" : entry.text) + "\t" + Field(anchor, "generation"));
    }
    private static string[] History(Context context) { return Property(Field(context.Log, "ht"), "HistoryText") as string[]; }
    private static bool Mode(Context context) { return (bool)context.Toggle.GetType().GetMethod("IsTranslatedMode").Invoke(context.Toggle, null); }
    private static void SetMode(Context context, bool translated)
    {
        if (Mode(context) != translated)
            if (!(bool)context.Toggle.GetType().GetMethod("HandleKey").Invoke(context.Toggle, new object[] { true }))
                throw new InvalidOperationException("正式F8共享路径拒绝切换");
        context.Toggle.GetType().GetMethod("HandleKey").Invoke(context.Toggle, new object[] { false });
        if (Mode(context) != translated) throw new InvalidOperationException("正式F8模式不符");
    }
    private static object Field(object value, string name) { return value.GetType().GetField(name, Members).GetValue(value); }
    private static object Property(object value, string name) { return value.GetType().GetProperty(name, Members).GetValue(value, null); }
    private static string Enc(string value) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? "")); }
    private static string Number(float value) { return value.ToString("R", CultureInfo.InvariantCulture); }
}
