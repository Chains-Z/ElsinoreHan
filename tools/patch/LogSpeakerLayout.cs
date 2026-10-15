using System;
using System.Reflection;
using HarmonyLib;
using TMPro;
using UnityEngine;

// 只修正日志姓名后的渲染缩进，不改原文、译文、历史或XUnity缓存。
public static class LogSpeakerLayout
{
    private const BindingFlags Fields = BindingFlags.Instance | BindingFlags.NonPublic;
    private static readonly FieldInfo advance = typeof(TMP_Text).GetField("m_xAdvance", Fields);
    private static readonly FieldInfo indent = typeof(TMP_Text).GetField("tag_Indent", Fields);
    private static readonly FieldInfo tag = typeof(TMP_Text).GetField("m_htmlTag", Fields);

    public static void Apply(Harmony harmony)
    {
        MethodInfo method = typeof(TMP_Text).GetMethod("ValidateHtmlTag", Fields);
        if (method == null || advance == null || indent == null || tag == null)
            throw new MissingMemberException("TMP日志缩进接口不兼容。");
        harmony.Patch(method, prefix: new HarmonyMethod(typeof(LogSpeakerLayout).GetMethod("BeforeTag")),
            postfix: new HarmonyMethod(typeof(LogSpeakerLayout).GetMethod("AfterTag")));
    }

    public static void BeforeTag(TMP_Text __instance, out float __state)
    {
        __state = (float)advance.GetValue(__instance);
    }

    public static void AfterTag(TMP_Text __instance, bool __result, float __state)
    {
        if (!__result || !(__instance is TextMeshProUGUI)) return;
        char[] parsed = tag.GetValue(__instance) as char[];
        const string expected = "indent=16%";
        if (parsed == null || parsed.Length <= expected.Length || parsed[expected.Length] != '\0') return;
        for (int index = 0; index < expected.Length; index++) if (parsed[index] != expected[index]) return;
        bool log = false;
        for (Transform parent = __instance.transform; parent != null; parent = parent.parent)
            if (parent.name == "LogCanvas") { log = true; break; }
        if (!log) return;
        float requested = (float)indent.GetValue(__instance);
        float resolved = ResolveIndent(requested, __state, __instance.fontSize);
        if (resolved <= requested) return;
        indent.SetValue(__instance, resolved);
        advance.SetValue(__instance, resolved);
    }

    public static float ResolveIndent(float requested, float nameEnd, float fontSize)
    {
        if (Single.IsNaN(nameEnd) || Single.IsInfinity(nameEnd) || Single.IsNaN(fontSize)
            || Single.IsInfinity(fontSize) || fontSize <= 0) return requested;
        return Math.Max(requested, nameEnd + fontSize * 0.25f);
    }
}
