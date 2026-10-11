using System;
using System.Collections;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 真实任务按钮与正式F8路径的背景回归，检查几何、颜色、监听和节点数量。
public static class LeadLayoutProbe
{
    private const BindingFlags Fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static object Read(object owner, string name)
    {
        for (Type type = owner.GetType(); type != null; type = type.BaseType)
        {
            var field = type.GetField(name, Fields | BindingFlags.DeclaredOnly);
            if (field != null) return field.GetValue(owner);
            var property = type.GetProperty(name, Fields | BindingFlags.DeclaredOnly);
            if (property != null) return property.GetValue(owner, null);
        }
        throw new MissingMemberException(owner.GetType().FullName, name);
    }
    private static string Enc(string text) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(text ?? "")); }
    private static void Write(StringBuilder report, string path, string line)
    {
        report.AppendLine(line);
        File.WriteAllText(path, report.ToString(), new UTF8Encoding(false));
    }
    private static int ListenerCount(object toggle)
    {
        var calls = Read(Read(toggle, "OnStateChange"), "m_Calls");
        return ((IList)Read(calls, "m_RuntimeCalls")).Count;
    }

    public static IEnumerator Capture(Component tab, string directory, Action<bool> setMode)
    {
        string path = Path.Combine(directory, "lead-layout.tsv");
        var report = new StringBuilder();
        var items = (IList)Read(tab, "currentLeadItems");
        if (items.Count < 2) throw new InvalidOperationException("任务布局回归缺少真实已获得任务。");
        // 改变一次真实选中任务，之后每次F8都须保留选择和颜色。
        var selected = Read(items[items.Count - 1], "Toggle");
        selected.GetType().GetProperty("IsOn", Fields).SetValue(selected, true, null);
        yield return new WaitForSecondsRealtime(0.5f);
        var colors = new Color[items.Count];
        var listeners = new int[items.Count];
        var sizes = new float[items.Count];
        for (int index = 0; index < items.Count; index++)
        {
            var text = (TMP_Text)Read(items[index], "Text");
            Component generator = FindGenerator(text);
            colors[index] = ((Image[])Read(generator, "splotches"))[0].color;
            listeners[index] = ListenerCount(Read(items[index], "Toggle"));
            sizes[index] = text.fontSize;
        }
        Write(report, path, "EXPECTED\t" + items.Count + "\t8");
        try
        {
            for (int mode = 0; mode < 8; mode++)
            {
                bool translated = mode % 2 == 0;
                setMode(translated);
                yield return new WaitForSecondsRealtime(0.5f);
                for (int index = 0; index < items.Count; index++)
                {
                    var text = (TMP_Text)Read(items[index], "Text");
                    Component generator = FindGenerator(text);
                    var rectangle = (RectTransform)generator.transform;
                    Vector2 target = rectangle.rect.size + (Vector2)Read(generator, "splotchExtrusion");
                    var images = (Image[])Read(generator, "splotches");
                    float left = float.PositiveInfinity, right = float.NegativeInfinity;
                    bool square = true, color = true, unique = true;
                    var ids = new System.Collections.Generic.HashSet<int>();
                    foreach (Image image in images)
                    {
                        Vector3[] corners = new Vector3[4];
                        image.rectTransform.GetWorldCorners(corners);
                        foreach (Vector3 corner in corners)
                        {
                            float x = rectangle.InverseTransformPoint(corner).x;
                            left = Math.Min(left, x); right = Math.Max(right, x);
                        }
                        square &= Math.Abs(image.rectTransform.rect.width - target.y) < 0.02f
                            && Math.Abs(image.rectTransform.rect.height - target.y) < 0.02f;
                        color &= image.color == colors[index];
                        unique &= ids.Add(image.GetInstanceID());
                    }
                    bool covers = right - left + 0.02f >= target.x;
                    float center = (left + right) / 2f - rectangle.rect.center.x;
                    bool nodes = generator.GetComponentsInChildren<Image>(true).Length == images.Length;
                    bool selection = (bool)Read(selected, "IsOn");
                    bool listener = ListenerCount(Read(items[index], "Toggle")) == listeners[index];
                    bool font = text.fontSize == sizes[index] && text.font.name == "Crimson" && !text.enableAutoSizing;
                    Write(report, path, "ITEM\t" + mode + "\t" + index + "\t" + Enc(text.text)
                        + "\t" + text.fontSize + "\t" + target.x + "\t" + target.y + "\t" + images.Length
                        + "\t" + left + "\t" + right + "\t" + center
                        + "\t" + covers + "\t" + square + "\t" + color + "\t" + unique + "\t" + nodes
                        + "\t" + selection + "\t" + listener + "\t" + font);
                }
            }
        }
        finally { setMode(true); }
        Write(report, path, "STATUS\tCOMPLETE");
    }

    private static Component FindGenerator(TMP_Text text)
    {
        foreach (Component component in text.transform.parent.GetComponents<Component>())
            if (component.GetType().FullName == "Elsinore.Ui.SplotchGenerator") return component;
        throw new InvalidOperationException("任务文字缺少真实墨迹背景。");
    }
}
