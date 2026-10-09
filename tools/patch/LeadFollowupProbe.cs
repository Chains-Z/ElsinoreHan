using System;
using System.Collections;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;

// 检查真实已显示线索，以及真实资源的格式组件重放；不修改获知条件或声称剧情E2E。
public static class LeadFollowupProbe
{
    private const BindingFlags Fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static object Read(object owner, string name)
    {
        var field = owner.GetType().GetField(name, Fields);
        if (field != null) return field.GetValue(owner);
        var property = owner.GetType().GetProperty(name, Fields);
        if (property == null) throw new MissingMemberException(owner.GetType().FullName, name);
        return property.GetValue(owner, null);
    }
    private static string Enc(string text) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(text ?? "")); }
    private static void Write(StringBuilder report, string path, string line)
    {
        report.AppendLine(line);
        File.WriteAllText(path, report.ToString(), new UTF8Encoding(false));
    }

    public static IEnumerator Capture(Component tab, string directory, Action<bool> setMode)
    {
        var path = Path.Combine(directory, "lead-followup.tsv");
        var report = new StringBuilder();
        var items = (IList)Read(tab, "currentLeadItems");
        var mapping = (IDictionary)Read(tab, "leadTextMapping");
        var body = (TMP_Text)Read(tab, "DescriptionText");
        var builder = (StringBuilder)Read(tab, "builder");
        Write(report, path, "EXPECTED_AVAILABLE\t" + items.Count);
        for (int i = 0; i < items.Count; i++)
        {
            var toggle = Read(items[i], "Toggle");
            toggle.GetType().GetProperty("IsOn", Fields).SetValue(toggle, true, null);
            yield return new WaitForSecondsRealtime(0.2f);
            string source = builder.ToString();
            string leadId = null;
            foreach (DictionaryEntry entry in mapping)
                if ("<line-height=90%>" + (string)Read(entry.Value, "Content") == source)
                {
                    if (leadId != null) throw new InvalidOperationException("真实线索组合来源存在歧义");
                    leadId = (string)entry.Key;
                }
            if (leadId == null) throw new InvalidOperationException("真实线索组件没有对应格式器来源");
            Write(report, path, "SOURCE\tavailable\t" + leadId + "\t" + Enc(source));
            yield return RoundTrip(report, path, "available", leadId, source, body, setMode);
        }
        string casePath = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_LEAD_CASES");
        if (String.IsNullOrEmpty(casePath) || !File.Exists(casePath)) throw new InvalidOperationException("缺少冻结线索组件重放文件");
        string original = builder.ToString();
        try
        {
            foreach (string line in File.ReadAllLines(casePath, Encoding.UTF8))
            {
                var fields = line.Split('\t');
                if (fields.Length != 3) throw new InvalidOperationException("线索重放文件格式异常");
                string content = Encoding.UTF8.GetString(Convert.FromBase64String(fields[1]));
                typeof(Elsinore.Ui.UiStrings).GetMethod("SetTextWithLineHeight", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
                    .Invoke(null, new object[] { body, builder, content });
                yield return new WaitForSecondsRealtime(0.2f);
                string source = builder.ToString();
                Write(report, path, "SOURCE\treplay\t" + fields[0] + "\t" + Enc(source));
                Write(report, path, "EXPECTED\treplay\t" + fields[0] + "\t" + fields[2]);
                yield return RoundTrip(report, path, "replay", fields[0], source, body, setMode);
            }
        }
        finally
        {
            setMode(true);
            // 只恢复显示组件的原始组合；业务数据一直未变。
            body.text = original;
            builder.Clear().Append(original);
        }
        Write(report, path, "STATUS\tCOMPLETE");
    }

    private static IEnumerator RoundTrip(StringBuilder report, string path, string kind, string id, string source, TMP_Text body, Action<bool> setMode)
    {
        string[] modes = { "translated", "original", "restored" };
        for (int i = 0; i < modes.Length; i++)
        {
            setMode(i != 1);
            yield return new WaitForSecondsRealtime(0.2f);
            Write(report, path, "TEXT\t" + kind + "\t" + id + "\t" + modes[i]
                + "\t" + body.GetInstanceID() + "\t" + body.gameObject.activeInHierarchy + "\t" + Enc(body.text));
        }
    }
}
