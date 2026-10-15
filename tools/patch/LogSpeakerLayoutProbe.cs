using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;

// 使用真实日志预制体重放真实资源片段，仅验证排版，不写入HistoryTracker。
public static class LogSpeakerLayoutProbe
{
    public static IEnumerator Capture(Component log, string outputDirectory)
    {
        string casesPath = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_LOG_SPEAKERS");
        if (String.IsNullOrEmpty(casesPath)) yield break;
        if (!Application.isBatchMode || String.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH")))
            throw new InvalidOperationException("日志姓名重放需要后台隔离保护。");
        MonoBehaviour toggle = null;
        foreach (MonoBehaviour item in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
            if (item != null && item.GetType().Name == "TranslationToggle") toggle = item;
        if (toggle == null) throw new InvalidOperationException("缺少正式切换插件。");
        var flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        TMP_Text prefab = log.GetType().GetField("TextPrefab", flags).GetValue(log) as TMP_Text;
        RectTransform content = (log.GetType().GetField("Content", flags).GetValue(log) as Component).transform as RectTransform;
        if (prefab == null || content == null || content.rect.width <= 0) throw new InvalidOperationException("缺少真实日志预制体或内容宽度。");
        bool initial = Mode(toggle);
        string reportPath = Path.Combine(outputDirectory, "log-speaker-layout.tsv");
        File.WriteAllText(reportPath, "SCHEMA\t1\n", new UTF8Encoding(false));
        TMP_Text clone = null;
        try
        {
            foreach (string line in File.ReadAllLines(casesPath))
            {
                string[] parts = line.Split('\t');
                if (parts.Length != 3) throw new InvalidDataException("日志重放输入格式错误。");
                string source = Encoding.UTF8.GetString(Convert.FromBase64String(parts[1]));
                foreach (float portion in new[] { 1f, 0.72f })
                {
                    SetMode(toggle, true);
                    for (int frame = 0; frame < 4; frame++) yield return null;
                    clone = UnityEngine.Object.Instantiate(prefab, log.transform, false);
                    clone.gameObject.name = "LogSpeakerLayoutReplay";
                    RectTransform rect = clone.rectTransform;
                    rect.anchorMin = rect.anchorMax = new Vector2(0.5f, 0.5f);
                    rect.pivot = new Vector2(0.5f, 0.5f);
                    rect.sizeDelta = new Vector2(content.rect.width * portion, 1600f);
                    clone.gameObject.SetActive(true);
                    clone.text = source;
                    float fontSize = clone.fontSize;
                    foreach (string phase in new[] { "translated", "original", "restored" })
                    {
                        SetMode(toggle, phase != "original");
                        for (int frame = 0; frame < 4; frame++) yield return null;
                        Canvas.ForceUpdateCanvases();
                        clone.ForceMeshUpdate();
                        string text = clone.text;
                        int body = text.IndexOf("<indent=16%>", StringComparison.Ordinal);
                        if (body < 0) throw new InvalidOperationException("重放日志缺少正文缩进标记。");
                        body += "<indent=16%>".Length;
                        float labelRight = Single.NegativeInfinity, bodyLeft = Single.NaN;
                        int labelLine = -1, bodyLine = -1;
                        for (int index = 0; index < clone.textInfo.characterCount; index++)
                        {
                            TMP_CharacterInfo item = clone.textInfo.characterInfo[index];
                            if (!item.isVisible) continue;
                            if (item.index < body) { labelRight = Math.Max(labelRight, item.topRight.x); labelLine = item.lineNumber; }
                            else if (bodyLine < 0) { bodyLeft = item.bottomLeft.x; bodyLine = item.lineNumber; }
                        }
                        string record = "SAMPLE\t" + parts[0] + "\t" + Number(portion) + "\t" + phase
                            + "\t" + Number(rect.rect.width) + "\t" + Number(fontSize) + "\t" + Number(clone.fontSize)
                            + "\t" + Number(labelRight) + "\t" + Number(bodyLeft) + "\t" + labelLine + "\t" + bodyLine
                            + "\t" + clone.GetInstanceID() + "\t" + Convert.ToBase64String(Encoding.UTF8.GetBytes(text));
                        File.AppendAllText(reportPath, record + "\n", new UTF8Encoding(false));
                    }
                    UnityEngine.Object.Destroy(clone.gameObject);
                    clone = null;
                }
            }
            File.AppendAllText(reportPath, "STATUS\tCOLLECTED\n", new UTF8Encoding(false));
        }
        finally
        {
            if (clone != null) UnityEngine.Object.Destroy(clone.gameObject);
            SetMode(toggle, initial);
        }
    }

    private static bool Mode(MonoBehaviour toggle) { return (bool)toggle.GetType().GetMethod("IsTranslatedMode").Invoke(toggle, null); }
    private static void SetMode(MonoBehaviour toggle, bool translated)
    {
        if (Mode(toggle) != translated) toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { true });
        toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { false });
        if (Mode(toggle) != translated) throw new InvalidOperationException("正式F8共享路径未完成模式切换。");
    }
    private static string Number(float value) { return value.ToString("R", CultureInfo.InvariantCulture); }
}
