using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

// 在已初始化的隔离游戏中调用真实格式器；只写独立builder，不修改业务历史。
public static class AmbientLogFormatterProbe
{
    [Serializable]
    public class Report
    {
        public bool passed;
        public int entries;
        public string input_sha256;
        public string actual_base64;
        public string expected_base64;
    }

    private static Type LoadedType(string name)
    {
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            var type = assembly.GetType(name);
            if (type != null) return type;
        }
        throw new InvalidOperationException("未加载真实类型：" + name);
    }

    public static void Run(object historyTracker, string directory)
    {
        string path = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_LOG_FORMATTER");
        if (String.IsNullOrEmpty(path)) return;
        var dialogue = LoadedType("Agakme.Scripting.DialogueAction");
        var action = LoadedType("Agakme.Scripting.RuntimeAction");
        var entry = LoadedType("Elsinore.Game.LogEntry");
        var format = historyTracker.GetType().GetMethod("formatEntry", BindingFlags.NonPublic | BindingFlags.Static);
        var report = new Report();
        using (var hash = SHA256.Create())
            report.input_sha256 = BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
        object previous = null;
        string expected = null;
        var builder = new StringBuilder();
        foreach (var line in File.ReadAllLines(path, Encoding.UTF8))
        {
            if (String.IsNullOrEmpty(line)) continue;
            var fields = line.Split('\t');
            var source = Encoding.UTF8.GetString(Convert.FromBase64String(fields[2]));
            if (fields[0] == "expected") { expected = source; continue; }
            var spoken = Activator.CreateInstance(dialogue, new object[] { fields[1], null, null, source });
            var current = entry.GetMethod("NewRuntimeAction").Invoke(null,
                new object[] { action.GetMethod("NewDialogue").Invoke(null, new object[] { spoken }) });
            if (fields[0] == "entry")
            {
                format.Invoke(null, new object[] { current, previous, builder });
                report.entries++;
            }
            else if (fields[0] != "previous") throw new InvalidOperationException("未知格式器输入类别");
            previous = current;
        }
        report.actual_base64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(builder.ToString()));
        report.expected_base64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(expected ?? ""));
        report.passed = report.entries == 4 && expected != null && builder.ToString() == expected;
        File.WriteAllText(Path.Combine(directory, "ambient-log-formatter.json"), JsonUtility.ToJson(report, true), new UTF8Encoding(false));
        if (!report.passed) throw new InvalidOperationException("真实格式器尾段与冻结源不一致");
    }
}
