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

// 使用真实文档入口、Scrollbar 和正式 F8 路径；只用于隔离后台测试。
public static class DocumentScrollAnchorProbe
{
    private const BindingFlags Members = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
    private sealed class Context
    {
        public Component Owner;
        public TMP_Text Body;
        public Scrollbar Scrollbar;
        public MonoBehaviour Toggle;
        public Type Helper;
        public string Id, Path, Source, Target;
        public bool InitialMode, InitialCaptured, Complete;
        public float InitialValue, Deadline;
        public void Line(string value) { File.AppendAllText(Path, value + "\n", new UTF8Encoding(false)); }
    }

    public static IEnumerator Capture(Component document, string id, string outputDirectory)
    {
        var context = new Context { Owner = document, Id = id,
            Path = System.IO.Path.Combine(outputDirectory, "document-scroll-anchor.tsv"),
            Deadline = Time.realtimeSinceStartup + 20f };
        if (!File.Exists(context.Path)) context.Line("SCHEMA\t1");
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
                    if (Time.realtimeSinceStartup > context.Deadline) throw new TimeoutException("文档滚动诊断超过20秒");
                    more = routines.Peek().MoveNext();
                    if (more) current = routines.Peek().Current;
                }
                catch (Exception error) { failure = error; }
                if (failure != null) { context.Line("FAILURE\t" + id + "\t" + Enc(failure.ToString())); break; }
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
                if (context.InitialCaptured) SetMode(context, context.InitialMode);
                // 取消仍排队的 F8 恢复，交回真实滚动条，不持续锁住阅读位置。
                if (context.Helper != null) context.Helper.GetMethod("Capture").Invoke(null, null);
                if (context.Scrollbar != null && context.InitialCaptured) context.Scrollbar.value = context.InitialValue;
            }
            catch (Exception error) { context.Complete = false; context.Line("FAILURE\t" + id + "\t" + Enc(error.ToString())); }
            context.Line("STATUS\t" + id + "\t" + (context.Complete ? "COLLECTED" : "FAILED"));
        }
    }

    private static IEnumerator Core(Context context)
    {
        if (!Application.isBatchMode || string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH")))
            throw new InvalidOperationException("文档滚动诊断缺少后台隔离");
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
        if (!saveGuard || !inputGuard || context.Toggle == null || context.Owner == null
            || context.Owner.GetType().FullName != "Elsinore.Ui.ObjectCloseupUI" || !context.Owner.gameObject.activeInHierarchy)
            throw new InvalidOperationException("真实文档入口/F8/存档保护不完整");
        context.Body = Field(context.Owner, "Body") as TMP_Text;
        context.Scrollbar = Field(context.Owner, "Scrollbar") as Scrollbar;
        context.Helper = context.Toggle.GetType().Assembly.GetType("LogScrollAnchor", true);
        context.Source = ((StringBuilder)Field(context.Owner, "builder")).ToString();
        context.InitialMode = Mode(context);
        context.InitialValue = context.Scrollbar.value;
        context.InitialCaptured = true;
        context.Line("GUARDS\t" + context.Id + "\t" + saveGuard + "\t" + inputGuard + "\tTrue");
        SetMode(context, true);
        for (int frame = 0; frame < 4; frame++) yield return null;
        context.Body.ForceMeshUpdate();
        context.Target = context.Body.text;
        context.Line("DOCUMENT\t" + context.Id + "\t" + context.Body.GetInstanceID()
            + "\t" + Enc(context.Source) + "\t" + Enc(context.Target));
        float[] positions = { 0.8f, 0.5f, 0.2f };
        foreach (float position in positions)
        {
            SetMode(context, true);
            for (int frame = 0; frame < 4; frame++) yield return null;
            context.Scrollbar.value = position;
            for (int frame = 0; frame < 4; frame++) yield return null;
            for (int leg = 0; leg < 2; leg++)
            {
                string mode = leg == 0 ? "original" : "restored";
                object before = context.Helper.GetMethod("Capture").Invoke(null, null);
                if (before == null || !(bool)Property(before, "IsDocument"))
                    throw new InvalidOperationException("真实文档没有 F8 段落锚点");
                Snapshot(context, position, mode, "before", before);
                SetMode(context, leg != 0);
                for (int frame = 0; frame < 5; frame++) yield return null;
                object after = context.Helper.GetField("LastCompleted").GetValue(null);
                if (after == null) throw new InvalidOperationException("正式 F8 路径无文档恢复记录");
                Snapshot(context, position, mode, "after", after);
            }
        }
        // F8 恢复结束后，正常移动滚动条仍须改变内容位置。
        float previousY = context.Body.rectTransform.anchoredPosition.y;
        context.Scrollbar.value = context.Scrollbar.value > 0.5f ? 0.1f : 0.9f;
        for (int frame = 0; frame < 4; frame++) yield return null;
        float newY = context.Body.rectTransform.anchoredPosition.y;
        context.Line("MANUAL_SCROLL\t" + context.Id + "\t" + Number(previousY) + "\t" + Number(newY));
        context.Complete = true;
    }

    private static void Snapshot(Context context, float position, string mode, string stage, object anchor)
    {
        object[] coordinate = { 0f };
        bool read = (bool)anchor.GetType().GetMethod("TryReadCurrentY").Invoke(anchor, coordinate);
        TMP_Text entry = Field(anchor, "entry") as TMP_Text;
        context.Line("SAMPLE\t" + context.Id + "\t" + Number(position) + "\t" + mode + "\t" + stage
            + "\t" + Property(anchor, "EntryInstanceId") + "\t" + Field(anchor, "ParagraphIndex")
            + "\t" + Number((float)Property(anchor, "CapturedY")) + "\t" + read + "\t" + Number((float)coordinate[0])
            + "\t" + Field(anchor, "Outcome") + "\t" + Number((float)Field(anchor, "RestoreError"))
            + "\t" + Mode(context) + "\t" + (entry != null && entry.gameObject.activeInHierarchy)
            + "\t" + Enc(entry == null ? "" : entry.text) + "\t" + Field(anchor, "generation")
            + "\t" + Property(anchor, "IsDocument") + "\t" + Enc((string)Field(anchor, "historySource")));
    }

    private static bool Mode(Context context) { return (bool)context.Toggle.GetType().GetMethod("IsTranslatedMode").Invoke(context.Toggle, null); }
    private static void SetMode(Context context, bool translated)
    {
        if (Mode(context) != translated && !(bool)context.Toggle.GetType().GetMethod("HandleKey").Invoke(context.Toggle, new object[] { true }))
            throw new InvalidOperationException("正式F8路径拒绝切换");
        context.Toggle.GetType().GetMethod("HandleKey").Invoke(context.Toggle, new object[] { false });
        if (Mode(context) != translated) throw new InvalidOperationException("正式F8模式不符");
    }
    private static object Field(object value, string name) { return value.GetType().GetField(name, Members).GetValue(value); }
    private static object Property(object value, string name) { return value.GetType().GetProperty(name, Members).GetValue(value, null); }
    private static string Enc(string value) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? "")); }
    private static string Number(float value) { return value.ToString("R", CultureInfo.InvariantCulture); }
}
