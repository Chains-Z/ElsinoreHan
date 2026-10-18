using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;
using System.Text;
using HarmonyLib;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 临时真实片尾UI集成探针；由既有RuntimeProbe先建立隔离存档与保存保护。
public static class CreditsSkipProbe
{
    private const string HarmonyId = "elsinorehan.runtimeprobe.creditsskip";
    private const BindingFlags Fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static MonoBehaviour controlled;
    private static bool suppressInput;
    private static bool preparationHeld;
    private static FieldInfo preparationState;
    private static int quitCalls, breakCalls, quitFrame, breakFrame;
    [Serializable] public sealed class CheckRow { public string name, detail; public bool passed; }
    [Serializable] public sealed class RingRow
    {
        public string state;
        public float progress, minimum_alpha, maximum_radius;
        public int vertices, triangles;
        public bool white;
    }
    [Serializable] public sealed class GlyphRow
    {
        public string character, font, atlas;
        public int material, atlas_width, atlas_height;
        public bool visible, white;
    }
    [Serializable] public sealed class Report
    {
        public int schema = 1, quit_calls, break_calls, trigger_frame, quit_frame, break_frame;
        public bool passed;
        public string scope = "真实Boss片尾入口、真实Start挂载及HandleKey组件集成；受控输入及开场准备延迟，后台主动刷新Canvas布局，不是物理按键或GPU像素验收";
        public string mesh_method = "真实CreditsSkipRing.OnPopulateMesh回调输出；Unity2018 CanvasRenderer没有GetMesh，未声称GPU已绘制";
        public string scene, text_translated, text_original, text_restored;
        public int screen_width, screen_height;
        public float[] label_screen_corners, ring_screen_corners;
        public List<CheckRow> checks = new List<CheckRow>();
        public List<RingRow> rings = new List<RingRow>();
        public List<GlyphRow> glyphs = new List<GlyphRow>();
    }
    private static void Check(Report report, string name, bool passed, string detail)
    {
        report.checks.Add(new CheckRow { name = name, passed = passed, detail = detail });
        if (!passed) throw new InvalidOperationException("片尾跳过集成检查失败：" + name + "；" + detail);
    }
    private static object Field(object instance, string name)
    {
        var field = instance.GetType().GetField(name, Fields);
        if (field == null) throw new MissingFieldException(instance.GetType().FullName, name);
        return field.GetValue(instance);
    }
    public static bool BlockAutomaticInput(MonoBehaviour __instance)
    {
        return !suppressInput;
    }
    // 只在隔离探针内延后原协程的正文准备，稳定复现开场时提示尚未就绪的窗口。
    public static bool HoldCreditsPreparation(object __instance, ref bool __result)
    {
        if (preparationHeld && (int)preparationState.GetValue(__instance) == 1)
        {
            __result = true;
            return false;
        }
        return true;
    }
    public static void RecordQuit() { quitCalls++; quitFrame = Time.frameCount; }
    public static void RecordBreak() { breakCalls++; breakFrame = Time.frameCount; }
    public static IEnumerable<CodeInstruction> ReplaceFinishCalls(IEnumerable<CodeInstruction> instructions)
    {
        int quits = 0, breaks = 0;
        var result = new List<CodeInstruction>();
        foreach (var instruction in instructions)
        {
            var called = instruction.operand as MethodInfo;
            if (called != null && called.DeclaringType == typeof(Application) && called.Name == "Quit" && called.GetParameters().Length == 0)
            {
                instruction.opcode = OpCodes.Call;
                instruction.operand = typeof(CreditsSkipProbe).GetMethod("RecordQuit");
                quits++;
            }
            else if (called != null && called.DeclaringType == typeof(Debug) && called.Name == "Break" && called.GetParameters().Length == 0)
            {
                instruction.opcode = OpCodes.Call;
                instruction.operand = typeof(CreditsSkipProbe).GetMethod("RecordBreak");
                breaks++;
            }
            result.Add(instruction);
        }
        if (quits != 1 || breaks != 1) throw new InvalidOperationException("片尾退出协程的Quit/Break调用契约改变");
        return result;
    }
    private static MonoBehaviour FindLive(Type type)
    {
        foreach (var item in Resources.FindObjectsOfTypeAll(type))
        {
            var component = item as MonoBehaviour;
            if (component != null && component.gameObject.scene.IsValid() && component.gameObject.scene.isLoaded
                && component.isActiveAndEnabled) return component;
        }
        return null;
    }
    private static bool Handle(MonoBehaviour skip, bool held, bool focused, double now)
    {
        return (bool)skip.GetType().GetMethod("HandleKey", Fields).Invoke(skip, new object[] { held, focused, now });
    }
    private static bool HoldThrough(MonoBehaviour skip, double from, double to)
    {
        for (double sample = from + 1.0 / 32; sample < to; sample += 1.0 / 32)
            if (Handle(skip, true, true, sample)) return true;
        return Handle(skip, true, true, to);
    }
    private static float Progress(Graphic ring)
    {
        return (float)ring.GetType().GetProperty("Progress").GetValue(ring, null);
    }
    private static bool White(Color32 color) { return color.r == 255 && color.g == 255 && color.b == 255 && color.a == 255; }
    public static MethodInfo PopulateMeshMethod(Type ringType)
    {
        return ringType.GetMethod("OnPopulateMesh", Fields, null, new Type[] { typeof(VertexHelper) }, null);
    }
    public static string SerializeReport(Report report)
    {
        var output = new StringBuilder("{");
        bool first = true;
        foreach (var field in typeof(Report).GetFields(BindingFlags.Instance | BindingFlags.Public))
        {
            if (!first) output.Append(','); first = false;
            output.Append(ItalicGeometryProbe.Serialize(field.Name)).Append(':');
            object value = field.GetValue(report);
            var list = value as IList;
            if (list != null && !(value is Array))
            {
                var values = new object[list.Count]; list.CopyTo(values, 0); value = values;
            }
            output.Append(ItalicGeometryProbe.Serialize(value));
        }
        return output.Append('}').ToString();
    }
    private static void CaptureRing(Report report, Graphic ring, string state, float expected)
    {
        Canvas.ForceUpdateCanvases();
        var row = new RingRow { state = state, progress = Progress(ring), white = true, minimum_alpha = 1 };
        var mesh = new Mesh();
        var helper = new VertexHelper();
        try
        {
            PopulateMeshMethod(ring.GetType()).Invoke(ring, new object[] { helper });
            helper.FillMesh(mesh);
            row.vertices = mesh.vertexCount; row.triangles = mesh.triangles.Length / 3;
            foreach (var color in mesh.colors32) { row.white &= White(color); row.minimum_alpha = Math.Min(row.minimum_alpha, color.a / 255f); }
            foreach (var point in mesh.vertices) row.maximum_radius = Math.Max(row.maximum_radius, new Vector2(point.x, point.y).magnitude);
            int segments = expected <= 0 ? 0 : Math.Max(1, Mathf.CeilToInt(64 * expected));
            report.rings.Add(row);
            Check(report, "ring_" + state, Math.Abs(row.progress - expected) < 0.0001f
                && row.vertices == (segments == 0 ? 0 : (segments + 1) * 2) && row.triangles == segments * 2
                && row.white && !ring.raycastTarget && (segments == 0 || row.maximum_radius > 0),
                "progress=" + row.progress + ";vertices=" + row.vertices + ";triangles=" + row.triangles + ";white=" + row.white);
        }
        finally { helper.Dispose(); UnityEngine.Object.DestroyImmediate(mesh); }
    }
    private static float[] Corners(RectTransform rect)
    {
        var points = new Vector3[4]; rect.GetWorldCorners(points);
        var result = new float[8];
        for (int i = 0; i < 4; i++)
        {
            Vector2 screen = RectTransformUtility.WorldToScreenPoint(null, points[i]);
            result[i * 2] = screen.x; result[i * 2 + 1] = screen.y;
        }
        return result;
    }
    private static bool BottomRight(float[] points)
    {
        if (Screen.width <= 0 || Screen.height <= 0) return false;
        for (int i = 0; i < 4; i++)
            if (points[i * 2] < Screen.width * 0.5f || points[i * 2] > Screen.width
                || points[i * 2 + 1] < 0 || points[i * 2 + 1] > Screen.height * 0.35f) return false;
        return true;
    }
    private static void CaptureGlyphs(Report report, TMP_Text label)
    {
        label.ForceMeshUpdate();
        bool valid = !label.isTextOverflowing && label.textInfo.characterCount > 0;
        for (int index = 0; index < label.textInfo.characterCount; index++)
        {
            var ch = label.textInfo.characterInfo[index];
            if (Char.IsWhiteSpace(ch.character)) continue;
            var atlas = ch.fontAsset == null || ch.fontAsset.atlasTextures == null || ch.fontAsset.atlasTextures.Length == 0
                ? null : ch.fontAsset.atlasTextures[0];
            var row = new GlyphRow { character = ch.character.ToString(), font = ch.fontAsset == null ? null : ch.fontAsset.name,
                atlas = atlas == null ? null : atlas.name, material = ch.materialReferenceIndex,
                atlas_width = atlas == null ? 0 : atlas.width, atlas_height = atlas == null ? 0 : atlas.height,
                visible = ch.isVisible, white = true };
            var geometry = label.textInfo.meshInfo[ch.materialReferenceIndex];
            var material = label.fontSharedMaterials[ch.materialReferenceIndex];
            row.white &= material != null && (!material.HasProperty("_FaceColor") || White((Color32)material.GetColor("_FaceColor")));
            for (int i = 0; i < 4; i++) row.white &= White(geometry.colors32[ch.vertexIndex + i]);
            valid &= row.visible && row.white && atlas != null && row.atlas_width > 0 && row.atlas_height > 0
                && ch.fontAsset.HasCharacter(ch.character)
                && ch.topRight.x > ch.bottomLeft.x && ch.topRight.y > ch.bottomLeft.y;
            report.glyphs.Add(row);
        }
        Check(report, "hint_actual_glyphs", valid, "逐字真实fontAsset/atlas/网格/颜色；characters=" + report.glyphs.Count);
    }
    private static void SetMode(MonoBehaviour toggle, bool translated)
    {
        if ((bool)toggle.GetType().GetMethod("IsTranslatedMode").Invoke(toggle, null) == translated) return;
        if (!(bool)toggle.GetType().GetMethod("HandleKey").Invoke(toggle, new object[] { true }))
            throw new InvalidOperationException("F8真实处理入口未切换");
    }
    public static IEnumerator Capture(string directory)
    {
        var report = new Report();
        var harmony = new Harmony(HarmonyId);
        MonoBehaviour player = null, toggle = null;
        object originalEnding = null;
        PropertyInfo selectedEnding = null;
        bool? originalMode = null;
        quitCalls = breakCalls = 0; quitFrame = breakFrame = -1;
        controlled = null; suppressInput = true;
        Directory.CreateDirectory(directory);
        try
        {
            var skipType = AccessTools.TypeByName("CreditsHoldSkip");
            var creditsType = AccessTools.TypeByName("Elsinore.Ui.CreditsPlayer");
            Check(report, "real_plugin_types", skipType != null && creditsType != null, "反射读取正式插件及游戏类型");
            MethodInfo finishMoveNext = null;
            foreach (var nested in skipType.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic))
                if (nested.Name.StartsWith("<FinishAfterFullRing>", StringComparison.Ordinal)) finishMoveNext = AccessTools.Method(nested, "MoveNext");
            Check(report, "finish_iterator_contract", finishMoveNext != null && finishMoveNext.ReturnType == typeof(bool), "定位正式插件真实退出协程");
            harmony.Patch(AccessTools.Method(skipType, "Update"), prefix: new HarmonyMethod(typeof(CreditsSkipProbe), "BlockAutomaticInput"));
            harmony.Patch(finishMoveNext, transpiler: new HarmonyMethod(typeof(CreditsSkipProbe), "ReplaceFinishCalls"));
            MethodInfo prepareMoveNext = null;
            foreach (var nested in creditsType.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic))
                if (nested.Name.StartsWith("<PlayCredits>", StringComparison.Ordinal))
                {
                    prepareMoveNext = AccessTools.Method(nested, "MoveNext");
                    preparationState = nested.GetField("<>1__state", Fields);
                }
            Check(report, "preparation_iterator_contract", prepareMoveNext != null && preparationState != null,
                "定位原游戏首次yield后、正文格式化之前的状态");
            preparationHeld = true;
            harmony.Patch(prepareMoveNext, prefix: new HarmonyMethod(typeof(CreditsSkipProbe), "HoldCreditsPreparation"));
            var tracker = ObjectTracker.Instance;
            Check(report, "real_boss_ready", tracker != null && tracker.Boss != null && tracker.Boss.IsGameInitialized, "使用ObjectTracker.Instance.Boss");
            selectedEnding = creditsType.GetProperty("SelectedEnding", BindingFlags.Public | BindingFlags.Static);
            originalEnding = selectedEnding.GetValue(null, null);
            selectedEnding.SetValue(null, Activator.CreateInstance(selectedEnding.PropertyType, new object[] { "END_Delusion" }), null);
            tracker.Boss.ActivateCredits();
            float deadline = Time.realtimeSinceStartup + 15;
            while (Time.realtimeSinceStartup < deadline)
            {
                player = FindLive(creditsType);
                controlled = player == null ? null : player.GetComponent(skipType) as MonoBehaviour;
                if (controlled != null && controlled.enabled && Field(controlled, "overlay") != null) break;
                yield return null;
            }
            Check(report, "real_credits_start", player != null && controlled != null && controlled.enabled,
                "真实ActivateCredits加载场景并经Start挂载插件");
            report.scene = player.gameObject.scene.name;
            Check(report, "credits_scene", report.scene == "credits", report.scene);
            var overlay = (GameObject)Field(controlled, "overlay");
            var canvas = overlay.GetComponent<Canvas>();
            var label = overlay.transform.Find("Hint/HintText").GetComponent<TMP_Text>();
            var ring = (Graphic)Field(controlled, "progressRing");
            Handle(controlled, false, true, 0);
            Handle(controlled, true, true, 0.1);
            bool earlyComplete = Handle(controlled, true, true, 0.7);
            Check(report, "loading_hold_does_not_accumulate", !earlyComplete && Progress(ring) == 0,
                "正文准备被暂缓时提前按住0.6秒；progress=" + Progress(ring));
            var readyProperty = skipType.GetProperty("PresentationReady");
            Check(report, "loading_overlay_not_ready", readyProperty != null && !(bool)readyProperty.GetValue(controlled, null)
                && !canvas.enabled, "正文准备前不显示提示，不允许暗中计时");
            yield return null;
            Check(report, "loading_long_hold_does_not_exit", !Handle(controlled, true, true, 5) && Progress(ring) == 0
                && quitCalls == 0 && breakCalls == 0, "等待超过长按时限仍保持零进度");
            preparationHeld = false;
            deadline = Time.realtimeSinceStartup + 10;
            while (!(bool)readyProperty.GetValue(controlled, null) && Time.realtimeSinceStartup < deadline)
            {
                // nographics没有正常渲染循环；与其它UI探针相同，显式执行真实Canvas布局回调。
                Canvas.ForceUpdateCanvases();
                yield return null;
            }
            Check(report, "prepared_overlay_ready", (bool)readyProperty.GetValue(controlled, null) && canvas.enabled,
                "原协程完成正文准备，提示完成布局且跨过首帧；prepared=" + Field(controlled, "creditsPrepared")
                + ";firstFrame=" + Field(controlled, "firstPresentationFrame") + ";currentFrame=" + Time.frameCount
                + ";canvas=" + canvas.enabled + ";hintCharacters=" + label.textInfo.characterCount);
            double readyNow = Math.Max(6, Time.realtimeSinceStartup);
            Check(report, "early_hold_restarts_at_zero", !Handle(controlled, true, true, readyNow) && Progress(ring) == 0,
                "无需松开加载期间新按下的Ctrl，显示就绪后从零起算");
            HoldThrough(controlled, readyNow, readyNow + 0.25);
            CaptureRing(report, ring, "startup_quarter", 0.25f);
            Handle(controlled, false, true, readyNow + 0.3);
            Check(report, "independent_overlay", overlay.activeInHierarchy && canvas.renderMode == RenderMode.ScreenSpaceOverlay
                && canvas.sortingOrder == 32760 && overlay.transform.parent == null, "真实独立根Canvas与排序");
            Check(report, "white_noninteractive_hint", label.color == Color.white && !label.raycastTarget
                && !ring.raycastTarget, "白字及非交互圆环");
            var track = overlay.transform.Find("Hint/Track").GetComponent<Graphic>();
            Check(report, "dark_gray_track", track.color == new Color(0.25f, 0.25f, 0.25f, 1) && !track.raycastTarget,
                "暗灰底环及非交互");
            toggle = FindLive(AccessTools.TypeByName("TranslationToggle"));
            Check(report, "real_toggle", toggle != null, "真实F8插件实例");
            originalMode = (bool)toggle.GetType().GetMethod("IsTranslatedMode").Invoke(toggle, null);
            SetMode(toggle, true);
            yield return new WaitForSecondsRealtime(0.3f);
            report.text_translated = label.text;
            Check(report, "hint_chinese", label.text == "长按 Ctrl 跳过", label.text);
            CaptureGlyphs(report, label);
            SetMode(toggle, false);
            yield return new WaitForSecondsRealtime(0.3f);
            report.text_original = label.text;
            Check(report, "hint_f8_original", label.text == "Hold Ctrl to skip", label.text);
            SetMode(toggle, true);
            yield return new WaitForSecondsRealtime(0.3f);
            report.text_restored = label.text;
            Check(report, "hint_f8_restored", label.text == "长按 Ctrl 跳过", label.text);
            Canvas.ForceUpdateCanvases(); label.ForceMeshUpdate();
            report.screen_width = Screen.width; report.screen_height = Screen.height;
            report.label_screen_corners = Corners(label.rectTransform); report.ring_screen_corners = Corners(ring.rectTransform);
            Check(report, "bottom_right_coordinates", BottomRight(report.label_screen_corners) && BottomRight(report.ring_screen_corners),
                "screen=" + Screen.width + "x" + Screen.height + ";label=" + label.rectTransform.rect + ";ring=" + ring.rectTransform.rect);
            double now = Time.realtimeSinceStartup;
            Handle(controlled, false, true, now);
            Handle(controlled, true, true, now + 0.1);
            Check(report, "quarter_not_complete", !HoldThrough(controlled, now + 0.1, now + 0.35), "受控32FPS输入25%");
            CaptureRing(report, ring, "quarter", 0.25f);
            Check(report, "half_not_complete", !HoldThrough(controlled, now + 0.35, now + 0.6), "受控32FPS输入50%");
            CaptureRing(report, ring, "half", 0.5f);
            bool longFrameComplete = Handle(controlled, true, true, now + 2.6);
            Check(report, "long_frame_does_not_complete", !longFrameComplete && Progress(ring) < 0.7f
                && quitCalls == 0 && breakCalls == 0, "半圈后注入2秒采样间隔；progress=" + Progress(ring)
                + ";complete=" + longFrameComplete);
            CaptureRing(report, ring, "stalled", 0.6f);
            Check(report, "long_frame_resumes_progress", !HoldThrough(controlled, now + 2.6, now + 2.7),
                "长帧后恢复正常采样，继续增长而不直接退出");
            CaptureRing(report, ring, "resumed", 0.7f);
            Check(report, "release_not_complete", !Handle(controlled, false, true, now + 2.8), "松开取消");
            CaptureRing(report, ring, "released", 0);
            now += 4;
            // 调用正式焦点事件，让暂停后台Update的情形也经过实际复位入口。
            AccessTools.Method(skipType, "OnApplicationFocus").Invoke(controlled, new object[] { false });
            Check(report, "preheld_needs_release", !Handle(controlled, true, true, now + 1)
                && !Handle(controlled, true, true, now + 3), "重新获得焦点时已按住不得累计");
            CaptureRing(report, ring, "preheld", 0);
            Handle(controlled, false, true, now + 4); Handle(controlled, true, true, now + 5);
            HoldThrough(controlled, now + 5, now + 5.5);
            Check(report, "unfocused_not_complete", !Handle(controlled, true, false, now + 10), "后台时间不能累计");
            CaptureRing(report, ring, "unfocused", 0);
            Check(report, "focus_return_still_held", !Handle(controlled, true, true, now + 11), "恢复焦点仍须释放");
            CaptureRing(report, ring, "focus_return", 0);
            Check(report, "no_early_exit", quitCalls == 0 && breakCalls == 0, "短按、松开及失焦均无退出回调");
            Handle(controlled, false, true, now + 12); Handle(controlled, true, true, now + 13);
            report.trigger_frame = Time.frameCount;
            Check(report, "full_hold_complete", HoldThrough(controlled, now + 13, now + 14), "连续1秒正常采样走真实HandleKey完成路径");
            CaptureRing(report, ring, "full", 1);
            Check(report, "full_ring_before_exit", quitCalls == 0 && breakCalls == 0, "原退出协程先yield一帧");
            for (int frame = 0; frame < 5 && (quitCalls == 0 || breakCalls == 0); frame++) yield return null;
            Check(report, "deferred_original_exit_calls", quitCalls == 1 && breakCalls == 1
                && quitFrame > report.trigger_frame && breakFrame > report.trigger_frame,
                "quit=" + quitCalls + ";break=" + breakCalls + ";triggerFrame=" + report.trigger_frame + ";quitFrame=" + quitFrame);
            Check(report, "repeat_does_not_complete", !Handle(controlled, true, true, now + 20)
                && !Handle(controlled, false, true, now + 21) && !Handle(controlled, true, true, now + 23), "完成后再按不重复退出");
            yield return null;
            Check(report, "exit_one_shot", quitCalls == 1 && breakCalls == 1, "两个测试回调各一次");
            report.passed = true;
        }
        finally
        {
            preparationHeld = false;
            // 卸除回调替换前取消全部待执行退出协程；不会在finally后真正退出或触发断点。
            try
            {
                if (controlled != null) controlled.StopAllCoroutines();
                if (player != null) player.StopAllCoroutines();
                if (toggle != null && originalMode.HasValue) SetMode(toggle, originalMode.Value);
                if (selectedEnding != null && originalEnding != null) selectedEnding.SetValue(null, originalEnding, null);
            }
            finally
            {
                try { harmony.UnpatchSelf(); }
                finally
                {
                    suppressInput = false; controlled = null;
                    report.quit_calls = quitCalls; report.break_calls = breakCalls;
                    report.quit_frame = quitFrame; report.break_frame = breakFrame;
                    File.WriteAllText(Path.Combine(directory, "credits-skip.json"), SerializeReport(report), new UTF8Encoding(false));
                }
            }
        }
    }
}
