using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using TMPro;
using UnityEngine;
using XUnity.AutoTranslator.Plugin.Core;

// 在隔离进程预置错误的完整缓存，验证同一个TMP控件重用和F8能修复；不打包。
public static class StrictLogCacheProbe
{
    public static void Run(string directory)
    {
        string path = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_STRICT_LOG_CASES");
        if (string.IsNullOrEmpty(path)) return;
        const BindingFlags members = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        var translator = AutoTranslator.Default;
        var cache = translator.GetType().GetField("TextCache", members).GetValue(translator);
        var overwrite = cache.GetType().GetMethod("AddTranslation", members);
        MonoBehaviour toggle = null;
        foreach (var item in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
            if (item != null && item.GetType().Name == "TranslationToggle") toggle = item;
        if (toggle == null) throw new InvalidOperationException("缓存回归缺少正式兼容插件");
        Type strictType = toggle.GetType().Assembly.GetType("StrictLogTranslation", true);
        var strict = Activator.CreateInstance(strictType, new object[] { translator });
        var resolve = strictType.GetMethod("Resolve");
        var handle = toggle.GetType().GetMethod("HandleKey");
        var mode = toggle.GetType().GetMethod("IsTranslatedMode");
        bool initialMode = (bool)mode.Invoke(toggle, null);
        var container = new GameObject("LogCanvas", typeof(RectTransform));
        var child = new GameObject("StrictLogCacheFixture", typeof(RectTransform), typeof(TextMeshProUGUI));
        child.transform.SetParent(container.transform, false);
        var text = child.GetComponent<TextMeshProUGUI>();
        foreach (var font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            if (font.name == "Crimson") { text.font = font; break; }
        text.fontSize = 32;
        var report = new StringBuilder("SCHEMA\t1\n");
        using (var hash = SHA256.Create())
            report.AppendLine("SOURCE_SHA256\t" + BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant());
        int count = 0; bool passed = true;
        try
        {
            if (!initialMode) handle.Invoke(toggle, new object[] { true });
            foreach (string line in File.ReadAllLines(path, Encoding.UTF8))
            {
                if (String.IsNullOrEmpty(line)) continue;
                var fields = line.Split('\t');
                string source = Encoding.UTF8.GetString(Convert.FromBase64String(fields[1]));
                string expected = Encoding.UTF8.GetString(Convert.FromBase64String(fields[2]));
                string mixed = "旧的部分译文\n" + source;
                overwrite.Invoke(cache, new object[] { source, mixed, -1 });
                string actual;
                bool seeded = translator.TryTranslate(source, out actual) && actual == mixed;
                text.SetText(new StringBuilder(source));
                bool repaired = translator.TryTranslate(source, out actual) && actual == expected && text.text == expected;
                handle.Invoke(toggle, new object[] { true });
                bool original = text.text == source;
                handle.Invoke(toggle, new object[] { true });
                bool restored = text.text == expected;
                bool complete = (string)resolve.Invoke(strict, new object[] { source }) == expected;
                bool valid = seeded && repaired && original && restored && complete;
                passed &= valid; count++;
                report.AppendLine("CASE\t" + fields[0] + "\t" + seeded + "\t" + repaired + "\t" + original + "\t" + restored + "\t" + complete);
            }
            string unknown = "<b>Othello:</b> <indent=16%>Dinner is served.\nUnreviewed internal marker.";
            bool rejected = resolve.Invoke(strict, new object[] { unknown }) == null;
            passed &= rejected;
            report.AppendLine("UNKNOWN_REJECTED\t" + rejected);
            report.AppendLine("SUMMARY\t" + passed + "\t" + count);
        }
        finally
        {
            if ((bool)mode.Invoke(toggle, null) != initialMode) handle.Invoke(toggle, new object[] { true });
            UnityEngine.Object.DestroyImmediate(child);
            UnityEngine.Object.DestroyImmediate(container);
            File.WriteAllText(Path.Combine(directory, "strict-log-cache.tsv"), report.ToString(), new UTF8Encoding(false));
        }
        if (!passed) throw new InvalidOperationException("完整日志缓存修复或F8回归失败");
    }
}
