using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 逐个通过真实头像入口检查当前人物介绍，不制造解锁状态或替换业务正文。
public static class BiographyScrollProbe
{
    private const BindingFlags Members = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static string path;
    private static object Field(object value, string name) { return value.GetType().GetField(name, Members).GetValue(value); }
    private static string Enc(string value) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? "")); }
    private static string Number(float value) { return value.ToString("R", CultureInfo.InvariantCulture); }

    public static IEnumerator Capture(Component tab, string actor, string directory)
    {
        if (path == null)
        {
            path = Path.Combine(directory, "biography-scroll.tsv");
            File.WriteAllText(path, "SCHEMA\t1\n", new UTF8Encoding(false));
        }
        TMP_Text body = Field(tab, "DescriptionText") as TMP_Text;
        ScrollRect scroll = body == null ? null : body.GetComponentInParent<ScrollRect>();
        if (!Application.isBatchMode || String.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH"))
            || scroll == null || scroll.content != body.rectTransform) throw new InvalidOperationException("人物滚动诊断缺少隔离保护或真实ScrollRect。");
        MonoBehaviour toggle = null;
        foreach (MonoBehaviour component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
            if (component != null && component.GetType().Name == "TranslationToggle") toggle = component;
        Type helper = toggle.GetType().Assembly.GetType("LogScrollAnchor", true);
        string source = ((StringBuilder)Field(tab, "builder")).ToString();
        bool initial = Mode(toggle);
        Vector2 position = scroll.content.anchoredPosition;
        try
        {
            foreach (string name in new[] { "middle", "bottom", "manual-away" })
            {
                SetMode(toggle, true);
                for (int frame = 0; frame < 3; frame++) yield return null;
                scroll.StopMovement();
                scroll.verticalNormalizedPosition = name == "bottom" ? 0 : name == "middle" ? 0.5f : 0.35f;
                for (int frame = 0; frame < 3; frame++) yield return null;
                string target = body.text;
                for (int leg = 0; leg < 2; leg++)
                {
                    object before = helper.GetMethod("Capture").Invoke(null, null);
                    if (before == null)
                    {
                        // 修前也独立采集真实段落，不能用没有保护的Capture冒称恢复成功。
                        RectTransform viewport = scroll.viewport == null ? scroll.transform as RectTransform : scroll.viewport;
                        MethodInfo capture = helper.GetMethod("CaptureEntry", BindingFlags.Static | BindingFlags.NonPublic, null,
                            new Type[] { typeof(Component), typeof(ScrollRect), typeof(RectTransform), typeof(TMP_Text), typeof(int), typeof(int), typeof(int), typeof(string), typeof(bool) }, null);
                        before = capture.Invoke(null, new object[] { tab, scroll, viewport, body, -1, 0, 1, source, true });
                    }
                    Sample(tab, actor, name, leg, "before", source, target, body, scroll, before);
                    SetMode(toggle, leg != 0);
                    for (int frame = 0; frame < 4; frame++) yield return null;
                    object after = helper.GetField("LastCompleted").GetValue(null);
                    Sample(tab, actor, name, leg, "after", source, target, body, scroll, after ?? before);
                }
            }
        }
        finally
        {
            SetMode(toggle, initial);
            helper.GetMethod("Capture").Invoke(null, null);
            scroll.StopMovement();
            scroll.content.anchoredPosition = position;
        }
    }

    private static void Sample(Component tab, string actor, string name, int leg, string stage, string source, string target,
                               TMP_Text body, ScrollRect scroll, object anchor)
    {
        if (anchor == null) throw new InvalidOperationException("人物介绍没有可观察的真实段落。");
        object[] output = { 0f };
        bool read = (bool)anchor.GetType().GetMethod("TryReadCurrentY").Invoke(anchor, output);
        var bio = anchor.GetType().GetProperty("IsBiography");
        string outcome = (string)Field(anchor, "Outcome");
        string record = "SAMPLE\t" + actor + "\t" + name + "\t" + leg + "\t" + stage
            + "\t" + body.GetInstanceID() + "\t" + Field(anchor, "generation") + "\t" + (bio != null && (bool)bio.GetValue(anchor, null))
            + "\t" + Field(anchor, "ParagraphIndex") + "\t" + Number((float)anchor.GetType().GetProperty("CapturedY").GetValue(anchor, null))
            + "\t" + read + "\t" + Number((float)output[0]) + "\t" + outcome + "\t" + Number((float)Field(anchor, "RestoreError"))
            + "\t" + Field(anchor, "PinnedToBottom") + "\t" + Number(scroll.verticalNormalizedPosition)
            + "\t" + Number(scroll.content.rect.height - (scroll.viewport == null ? (scroll.transform as RectTransform).rect.height : scroll.viewport.rect.height))
            + "\t" + Enc(source) + "\t" + Enc(target) + "\t" + Enc(body.text) + "\t" + Enc(((StringBuilder)Field(tab, "builder")).ToString());
        File.AppendAllText(path, record + "\n", new UTF8Encoding(false));
    }

    public static void Complete() { File.AppendAllText(path, "STATUS\tCOLLECTED\n", new UTF8Encoding(false)); }
    private static bool Mode(MonoBehaviour toggle) { return (bool)toggle.GetType().GetMethod("IsTranslatedMode").Invoke(toggle, null); }
    private static void SetMode(MonoBehaviour toggle, bool translated)
    {
        if (Mode(toggle) != translated) toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { true });
        toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { false });
        if (Mode(toggle) != translated) throw new InvalidOperationException("人物介绍F8模式切换失败。");
    }
}
