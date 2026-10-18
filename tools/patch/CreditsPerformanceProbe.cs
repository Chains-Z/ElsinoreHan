using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using HarmonyLib;
using TMPro;
using UnityEngine;

// 临时隔离诊断：记录真实片尾的CPU方法耗时与自然帧间隔，不伪造卡顿输入。
public static class CreditsPerformanceProbe
{
    private const BindingFlags Methods = BindingFlags.Instance | BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
    private static bool recording;
    private static readonly Dictionary<MethodBase, MethodRow> timings = new Dictionary<MethodBase, MethodRow>();
    private static readonly List<CallRow> slow = new List<CallRow>();
    public sealed class MethodRow { public string method; public int calls, maximum_frame; public float total_ms, maximum_ms; }
    public sealed class CallRow { public string method; public int frame; public float ms; }
    public sealed class FrameRow { public int frame, gc0, gc1, gc2, memory_kb, target_fps, vsync; public float interval_ms, canvas_ms; }
    public sealed class Report
    {
        public bool passed;
        public string mode, error, scope = "真实片尾CPU方法和自然帧间隔采样；无图形后台显式刷新Canvas，不是GPU或实际玩家停顿的录制";
        public string body_font, body_sha256, body_input_sha256;
        public int body_source_characters, body_rendered_characters, body_vertices;
        public int maximum_rich_text_parts, maximum_context_references;
        public bool body_auto_sizing, ten_fps_enforced;
        public float body_font_size, capture_ms, activate_ms;
        public MethodRow[] methods;
        public CallRow[] slow_calls;
        public FrameRow[] frames;
        public string[] notes;
    }
    private static int maximumRichParts, maximumContextReferences;
    private static string bodyInputHash;
    private static string Hash(string value)
    {
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value))).Replace("-", "").ToLowerInvariant();
    }
    public static void CaptureBodyInput(StringBuilder __1)
    {
        if (recording && __1 != null && __1.Length > 100000) bodyInputHash = Hash(__1.ToString());
    }
    public static void CaptureRichResult(object __result)
    {
        if (!recording || __result == null) return;
        var property = __result.GetType().GetProperty("Arguments");
        var arguments = property == null ? null : property.GetValue(__result, null) as IEnumerable;
        if (arguments == null) return;
        int parts = 0, references = 0;
        foreach (var argument in arguments)
        {
            parts++;
            var info = argument.GetType().GetProperty("Info").GetValue(argument, null);
            foreach (string field in new string[] { "ContextBefore", "ContextAfter" })
            {
                var context = info.GetType().GetProperty(field).GetValue(info, null) as ICollection;
                if (context != null) references += context.Count;
            }
        }
        maximumRichParts = Math.Max(maximumRichParts, parts);
        maximumContextReferences = Math.Max(maximumContextReferences, references);
    }
    public static bool BlockInput() { return false; }
    public static void LimitFrameRate() { Application.targetFrameRate = 10; }
    public static void Begin(out long __state) { __state = recording ? Stopwatch.GetTimestamp() : 0; }
    public static void End(MethodBase __originalMethod, long __state)
    {
        if (__state == 0) return;
        float ms = (float)((Stopwatch.GetTimestamp() - __state) * 1000.0 / Stopwatch.Frequency);
        MethodRow row = timings[__originalMethod];
        row.calls++; row.total_ms += ms;
        if (ms > row.maximum_ms) { row.maximum_ms = ms; row.maximum_frame = Time.frameCount; }
        if (ms >= 2 && slow.Count < 500) slow.Add(new CallRow { method = row.method, frame = Time.frameCount, ms = ms });
    }
    private static void Patch(Harmony harmony, MethodInfo method, List<string> notes)
    {
        if (method == null || method.IsAbstract || method.ContainsGenericParameters || method.GetMethodBody() == null || timings.ContainsKey(method)) return;
        string name = method.DeclaringType.FullName + "." + method.Name + "(";
        foreach (var parameter in method.GetParameters()) name += parameter.ParameterType.Name + ",";
        name += ")";
        try
        {
            timings[method] = new MethodRow { method = name };
            harmony.Patch(method, prefix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "Begin"),
                postfix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "End"));
        }
        catch (Exception error) { timings.Remove(method); notes.Add(name + ":" + error.GetType().Name); }
    }
    private static void PatchNames(Harmony harmony, Type type, List<string> notes, params string[] names)
    {
        if (type == null) return;
        foreach (var method in type.GetMethods(Methods))
            if (Array.IndexOf(names, method.Name) >= 0) Patch(harmony, method, notes);
    }
    private static MonoBehaviour Find(Type type)
    {
        if (type == null) return null;
        foreach (var value in Resources.FindObjectsOfTypeAll(type))
        {
            var component = value as MonoBehaviour;
            if (component != null && component.isActiveAndEnabled && component.gameObject.scene.IsValid()
                && component.gameObject.scene.isLoaded) return component;
        }
        return null;
    }
    private static void Mode(MonoBehaviour toggle, bool translated)
    {
        if (toggle == null) return;
        if ((bool)toggle.GetType().GetMethod("IsTranslatedMode").Invoke(toggle, null) != translated)
            toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { true });
    }
    public static IEnumerator Capture(string directory)
    {
        var report = new Report { mode = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_CREDITS_PROFILE") };
        var harmony = new Harmony("elsinorehan.runtimeprobe.creditsperformance");
        var frames = new List<FrameRow>(); var notes = new List<string>();
        MonoBehaviour player = null, toggle = null; object originalEnding = null;
        PropertyInfo ending = null; bool? originalMode = null;
        int originalFps = Application.targetFrameRate;
        timings.Clear(); slow.Clear(); maximumRichParts = maximumContextReferences = 0; bodyInputHash = null;
        var capture = new Stopwatch();
        try
        {
            var creditsType = AccessTools.TypeByName("Elsinore.Ui.CreditsPlayer");
            var skipType = AccessTools.TypeByName("CreditsHoldSkip");
            var toggleType = AccessTools.TypeByName("TranslationToggle");
            if (creditsType == null) throw new MissingMemberException("CreditsPlayer");
            // 片尾Start会把帧率重新设为60；在同一帧的后置挂钩恢复隔离测试的10FPS约束。
            harmony.Patch(AccessTools.Method(creditsType, "Start"), postfix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "LimitFrameRate"));
            LimitFrameRate(); report.ten_fps_enforced = true;
            if (skipType != null) harmony.Patch(AccessTools.Method(skipType, "Update"), prefix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "BlockInput"));
            if (toggleType != null) harmony.Patch(AccessTools.Method(toggleType, "Update"), prefix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "BlockInput"));
            PatchNames(harmony, typeof(TextMeshProUGUI), notes, "GenerateTextMesh", "OnPreRenderCanvas");
            PatchNames(harmony, typeof(TMP_Text), notes, "get_preferredHeight", "GetPreferredHeight", "CalculatePreferredValues", "ParseInputText");
            PatchNames(harmony, toggleType, notes, "PrepareOfflineText", "SetBuilderThroughText");
            if (toggleType != null) harmony.Patch(AccessTools.Method(toggleType, "SetBuilderThroughText"),
                prefix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "CaptureBodyInput"));
            PatchNames(harmony, skipType, notes, "AfterStart", "MarkCreditsPrepared", "HandleKey");
            PatchNames(harmony, AccessTools.TypeByName("Elsinore.Game.Credits"), notes, "formatCredits");
            PatchNames(harmony, AccessTools.TypeByName("XUnity.AutoTranslator.Plugin.Core.AutoTranslationPlugin"), notes,
                "Update", "LateUpdate", "TryTranslate", "HandleTextChanged", "OnTextChanged",
                "TranslateOrQueueWebJob", "TranslateOrQueueWebJobImmediate", "TranslateByEndpoint", "TranslateByParserResult",
                "TranslateOrQueueWebJobImmediateByParserResult");
            PatchNames(harmony, AccessTools.TypeByName("XUnity.AutoTranslator.Plugin.Core.TextTranslationCache"), notes, "TryGetTranslation");
            var translatorType = AccessTools.TypeByName("XUnity.AutoTranslator.Plugin.Core.AutoTranslationPlugin");
            if (translatorType != null)
                foreach (var nested in translatorType.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic))
                    Patch(harmony, AccessTools.Method(nested, "MoveNext"), notes);
            var richType = AccessTools.TypeByName("XUnity.AutoTranslator.Plugin.Core.Parsing.RichTextParser");
            PatchNames(harmony, richType, notes, "Parse");
            if (richType != null) harmony.Patch(AccessTools.Method(richType, "Parse"),
                postfix: new HarmonyMethod(typeof(CreditsPerformanceProbe), "CaptureRichResult"));
            PatchNames(harmony, AccessTools.TypeByName("XUnity.AutoTranslator.Plugin.Core.Parsing.RegexSplittingTextParser"), notes, "Parse");
            PatchNames(harmony, AccessTools.TypeByName("XUnity.AutoTranslator.Plugin.Core.UntranslatedText"), notes,
                "PerformInternalTrimming", "PrepareUntranslatedText", "FixTranslatedText");
            foreach (var nested in creditsType.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic))
                if (nested.Name.StartsWith("<PlayCredits>", StringComparison.Ordinal)) Patch(harmony, AccessTools.Method(nested, "MoveNext"), notes);
            toggle = Find(toggleType);
            if (toggle != null) originalMode = (bool)toggleType.GetMethod("IsTranslatedMode").Invoke(toggle, null);
            Mode(toggle, !report.mode.StartsWith("original", StringComparison.Ordinal));
            ending = creditsType.GetProperty("SelectedEnding", BindingFlags.Static | BindingFlags.Public);
            originalEnding = ending.GetValue(null, null);
            ending.SetValue(null, Activator.CreateInstance(ending.PropertyType, new object[] { "END_Delusion" }), null);
            recording = true; capture.Start();
            var activate = Stopwatch.StartNew(); ObjectTracker.Instance.Boss.ActivateCredits();
            report.activate_ms = (float)activate.Elapsed.TotalMilliseconds;
            long last = Stopwatch.GetTimestamp();
            while (capture.Elapsed.TotalSeconds < 8 || frames.Count < 12)
            {
                long now = Stopwatch.GetTimestamp();
                var frame = new FrameRow { frame = Time.frameCount,
                    interval_ms = (float)((now - last) * 1000.0 / Stopwatch.Frequency),
                    target_fps = Application.targetFrameRate, vsync = QualitySettings.vSyncCount,
                    gc0 = GC.CollectionCount(0), gc1 = GC.CollectionCount(1), gc2 = GC.CollectionCount(2),
                    memory_kb = (int)(GC.GetTotalMemory(false) / 1024) };
                last = now;
                var canvas = Stopwatch.StartNew(); Canvas.ForceUpdateCanvases();
                frame.canvas_ms = (float)canvas.Elapsed.TotalMilliseconds; frames.Add(frame);
                report.ten_fps_enforced &= frame.target_fps == 10;
                player = Find(creditsType);
                if (player != null)
                {
                    var body = AccessTools.Field(creditsType, "TextField").GetValue(player) as TMP_Text;
                    if (body != null)
                    {
                        report.body_source_characters = body.text == null ? 0 : body.text.Length;
                        report.body_font = body.font == null ? null : body.font.name;
                        report.body_auto_sizing = body.enableAutoSizing; report.body_font_size = body.fontSize;
                        report.body_rendered_characters = body.textInfo.characterCount;
                        int vertices = 0; foreach (var mesh in body.textInfo.meshInfo) vertices += mesh.vertexCount;
                        report.body_vertices = vertices;
                    }
                }
                yield return null;
            }
            if (player != null)
            {
                var body = AccessTools.Field(creditsType, "TextField").GetValue(player) as TMP_Text;
                report.body_sha256 = Hash(body.text);
                report.body_input_sha256 = bodyInputHash;
            }
            report.passed = player != null && report.body_source_characters > 0 && report.body_rendered_characters > 0 && report.ten_fps_enforced;
            if (!report.passed) report.error = "没有采集到真实片尾正文与文字网格";
        }
        finally
        {
            recording = false; capture.Stop(); report.capture_ms = (float)capture.Elapsed.TotalMilliseconds;
            report.maximum_rich_text_parts = maximumRichParts; report.maximum_context_references = maximumContextReferences;
            if (player != null) player.StopAllCoroutines();
            if (toggle != null && originalMode.HasValue) Mode(toggle, originalMode.Value);
            if (ending != null && originalEnding != null) ending.SetValue(null, originalEnding, null);
            harmony.UnpatchSelf();
            Application.targetFrameRate = originalFps;
            report.methods = new List<MethodRow>(timings.Values).ToArray();
            report.slow_calls = slow.ToArray(); report.frames = frames.ToArray(); report.notes = notes.ToArray();
            File.WriteAllText(Path.Combine(directory, "credits-skip.json"), ItalicGeometryProbe.Serialize(report), new UTF8Encoding(false));
        }
    }
}
