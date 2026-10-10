using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;

// 只在隔离副本的真实头像入口重放资源正文，不改变人物获知条件或存档。
public static class BiographyReplayProbe
{
    private const BindingFlags Members = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private sealed class Case { public string Id, Actor, Source, Target; }
    private static List<Case> cases;
    private static readonly HashSet<string> visited = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    private static string path;
    private static string Enc(string value) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? "")); }
    private static string Dec(string value) { return Encoding.UTF8.GetString(Convert.FromBase64String(value)); }
    private static object Field(object owner, string name) { return owner.GetType().GetField(name, Members).GetValue(owner); }
    private static void Line(string value) { File.AppendAllText(path, value + "\n", new UTF8Encoding(false)); }

    private static void Load(string directory)
    {
        if (cases != null) return;
        string input = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BIOGRAPHY_CASES");
        if (String.IsNullOrEmpty(input) || !File.Exists(input)) throw new InvalidOperationException("缺少人物资料真实资源重放文件");
        cases = new List<Case>();
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (string line in File.ReadAllLines(input, Encoding.UTF8))
        {
            var fields = line.Split('\t');
            if (fields.Length != 4 || fields[0].Length == 0 || fields[3].Length == 0 || !ids.Add(fields[0]))
                throw new InvalidOperationException("人物资料重放文件格式或ID异常");
            var item = new Case { Id = fields[0], Source = Dec(fields[1]), Target = Dec(fields[2]), Actor = fields[3] };
            if (item.Source.Length == 0 || !item.Target.StartsWith("<line-height=90%>", StringComparison.Ordinal))
                throw new InvalidOperationException("人物资料重放正文为空或缺少真实行高格式");
            cases.Add(item);
        }
        if (cases.Count == 0) throw new InvalidOperationException("人物资料重放文件为空");
        path = Path.Combine(directory, "biography-replay.tsv");
        File.WriteAllText(path, "SCHEMA\t1\nSCOPE\treal_resource_component_replay\n", new UTF8Encoding(false));
        using (var sha = System.Security.Cryptography.SHA256.Create())
            Line("INPUT_SHA256\t" + BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(input))).Replace("-", "").ToLowerInvariant());
        foreach (Case item in cases) Line("EXPECTED\t" + item.Id + "\t" + item.Actor + "\t" + Enc(item.Source) + "\t" + Enc(item.Target));
    }

    public static IEnumerator Capture(Component tab, string actor, string directory)
    {
        Load(directory);
        if (!visited.Add(actor)) throw new InvalidOperationException("人物资料头像重复访问：" + actor);
        TMP_Text body = Field(tab, "DescriptionText") as TMP_Text;
        TMP_Text title = Field(tab, "TitleText") as TMP_Text;
        TMP_Text subtitle = Field(tab, "SlugText") as TMP_Text;
        var builder = Field(tab, "builder") as StringBuilder;
        MonoBehaviour toggle = null;
        bool saveGuard = false, inputGuard = false;
        foreach (MonoBehaviour component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
        {
            if (component == null) continue;
            if (component.GetType().Name == "TranslationToggle") toggle = component;
            if (component.GetType().Name == "RuntimeProbe")
            {
                saveGuard = (bool)Field(component, "saveGuardActive");
                inputGuard = (bool)component.GetType().GetField("physicalInputGuardActive", BindingFlags.Static | BindingFlags.NonPublic).GetValue(null);
            }
        }
        if (!Application.isBatchMode || String.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH"))
            || !saveGuard || !inputGuard || toggle == null || body == null || title == null || subtitle == null || builder == null
            || !tab.gameObject.activeInHierarchy || !body.gameObject.activeInHierarchy || tab.GetType().Name != "JournalCharactersTab")
            throw new InvalidOperationException("人物资料重放缺少真实组件入口或后台存档保护");
        Line("CONTROL\t" + actor + "\t" + body.GetInstanceID() + "\tTrue\tTrue\tTrue");
        string initialSource = builder.ToString(), initialBody = body.text, initialTitle = title.text, initialSubtitle = subtitle.text;
        bool initialMode = Mode(toggle), complete = false;
        var setter = typeof(Elsinore.Ui.UiStrings).GetMethod("SetTextWithLineHeight", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic,
            null, new Type[] { typeof(TextMeshProUGUI), typeof(StringBuilder), typeof(string) }, null);
        if (setter == null) throw new MissingMethodException("真实人物正文 SetTextWithLineHeight 签名不匹配");
        try
        {
            foreach (Case item in cases)
            {
                if (!String.Equals(item.Actor, actor, StringComparison.OrdinalIgnoreCase)) continue;
                SetMode(toggle, true);
                setter.Invoke(null, new object[] { body, builder, item.Source });
                for (int frame = 0; frame < 3; frame++) yield return null;
                string source = builder.ToString();
                if (source != "<line-height=90%>" + item.Source) throw new InvalidOperationException("真实人物格式器改变冻结资源正文");
                Line("SOURCE\t" + item.Id + "\t" + actor + "\t" + body.GetInstanceID() + "\t" + Enc(source));
                string[] modes = { "translated", "original", "restored" };
                for (int mode = 0; mode < modes.Length; mode++)
                {
                    SetMode(toggle, mode != 1);
                    for (int frame = 0; frame < 3; frame++) yield return null;
                    Line("TEXT\t" + item.Id + "\t" + modes[mode] + "\t" + body.GetInstanceID() + "\t" + body.gameObject.activeInHierarchy
                        + "\t" + Enc(body.text) + "\t" + Enc(builder.ToString()) + "\t" + Mode(toggle));
                    if (mode == 0) Lookup(item.Id, source, body.text);
                }
            }
            complete = true;
        }
        finally
        {
            // 恢复原始格式器组合与原语言；不把中文写入人物资源或业务状态。
            builder.Clear().Append(initialSource);
            body.text = initialSource;
            SetMode(toggle, initialMode);
            if (!complete) Line("ACTOR_STATUS\t" + actor + "\tFAILED");
        }
        // 正常路径等待真实消费者完成恢复，再断言原显示；finally 在失败时也先恢复原组合。
        for (int frame = 0; frame < 3; frame++) yield return null;
        Line("RESTORE\t" + actor + "\t" + body.GetInstanceID() + "\t" + Enc(initialSource) + "\t" + Enc(builder.ToString())
            + "\t" + Enc(initialBody) + "\t" + Enc(body.text) + "\t" + (title.text == initialTitle)
            + "\t" + (subtitle.text == initialSubtitle) + "\t" + (Mode(toggle) == initialMode));
        Line("ACTOR_STATUS\t" + actor + "\tCOLLECTED");
    }

    public static void Complete(string directory)
    {
        Load(directory);
        foreach (Case item in cases) if (!visited.Contains(item.Actor)) Line("UNAVAILABLE\t" + item.Id + "\t" + item.Actor + "\tno_frozen_portrait");
        Line("STATUS\tCOLLECTED");
    }

    private static void Lookup(string id, string source, string display)
    {
        Type api = null;
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            api = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.AutoTranslator", false);
            if (api != null) break;
        }
        if (api == null) throw new InvalidOperationException("真实人物翻译缓存API不存在");
        var translator = api.GetProperty("Default").GetValue(null, null);
        var contract = api.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.ITranslator");
        var lookup = contract.GetMethod("TryTranslate", new Type[] { typeof(string), typeof(string).MakeByRefType() });
        var arguments = new object[] { source, null };
        bool found = (bool)lookup.Invoke(translator, arguments);
        Line("API\t" + id + "\t" + found + "\t" + Enc(arguments[1] as string) + "\t" + Enc(display));
    }
    private static bool Mode(MonoBehaviour toggle) { return (bool)toggle.GetType().GetMethod("IsTranslatedMode").Invoke(toggle, null); }
    private static void SetMode(MonoBehaviour toggle, bool translated)
    {
        if (Mode(toggle) != translated && !(bool)toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { true }))
            throw new InvalidOperationException("真实人物F8入口拒绝切换");
        toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { false });
        if (Mode(toggle) != translated) throw new InvalidOperationException("真实人物F8模式不符");
    }
}
