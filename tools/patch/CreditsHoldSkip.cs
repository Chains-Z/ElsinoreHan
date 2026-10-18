using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using XUnity.AutoTranslator.Plugin.Core;

// 仅在原CreditsPlayer完成Start后附加；保留原输入、滚动及音乐快进逻辑。
public sealed class CreditsHoldSkip : MonoBehaviour
{
    public const string HintSource = "Hold Ctrl to skip";
    private MonoBehaviour player;
    private GameObject overlay;
    private CreditsSkipRing progressRing;
    private TMP_Text hintLabel;
    private TMP_Text creditsBody;
    private static readonly HashSet<TMP_Text> creditsBodies = new HashSet<TMP_Text>();
    private static FieldInfo stabilizationUi, stabilizationInfo;
    private static PropertyInfo stabilizationFlag;
    private bool creditsPrepared;
    private int firstPresentationFrame = -1;
    private bool completionQueued;
    private readonly CreditsSkipGesture gesture = new CreditsSkipGesture();

    public static void Apply(Harmony harmony)
    {
        Type type = AccessTools.TypeByName("Elsinore.Ui.CreditsPlayer");
        var start = type == null ? null : AccessTools.Method(type, "Start", Type.EmptyTypes);
        var play = type == null ? null : AccessTools.Method(type, "PlayCredits", Type.EmptyTypes);
        if (start == null || start.ReturnType != typeof(void) || play == null || play.ReturnType != typeof(IEnumerator)
            || !typeof(MonoBehaviour).IsAssignableFrom(type))
            throw new MissingMethodException("CreditsPlayer.Start/PlayCredits");
        var translatorType = typeof(AutoTranslator).Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.AutoTranslationPlugin", true);
        MethodInfo stabilization = null;
        foreach (var nested in translatorType.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic))
        {
            if (!nested.Name.StartsWith("<WaitForTextStablization>", StringComparison.Ordinal)) continue;
            var ui = AccessTools.Field(nested, "ui");
            var info = AccessTools.Field(nested, "info");
            if (ui == null || ui.FieldType != typeof(object) || info == null
                || info.FieldType.FullName != "XUnity.AutoTranslator.Plugin.Core.TextTranslationInfo") continue;
            if (stabilization != null) throw new AmbiguousMatchException("XUnity文字稳定组件协程不唯一");
            stabilization = AccessTools.Method(nested, "MoveNext");
            stabilizationUi = ui; stabilizationInfo = info;
            stabilizationFlag = info.FieldType.GetProperty("IsStabilizingText");
        }
        if (stabilization == null || stabilization.ReturnType != typeof(bool) || stabilizationFlag == null || !stabilizationFlag.CanWrite)
            throw new MissingMethodException("XUnity.WaitForTextStablization组件协程");
        harmony.Patch(stabilization, prefix: new HarmonyMethod(typeof(CreditsHoldSkip), "ContinueStabilization"));
        harmony.Patch(start, postfix: new HarmonyMethod(typeof(CreditsHoldSkip), "AfterStart"),
            transpiler: new HarmonyMethod(typeof(CreditsHoldSkip), "WrapPreparation"));
    }
    public static IEnumerable<CodeInstruction> WrapPreparation(IEnumerable<CodeInstruction> instructions)
    {
        int matches = 0;
        foreach (var instruction in instructions)
        {
            yield return instruction;
            var called = instruction.operand as MethodInfo;
            if ((instruction.opcode == OpCodes.Call || instruction.opcode == OpCodes.Callvirt) && called != null
                && called.DeclaringType.FullName == "Elsinore.Ui.CreditsPlayer" && called.Name == "PlayCredits"
                && called.ReturnType == typeof(IEnumerator) && called.GetParameters().Length == 0)
            {
                // 在Start的实际调用点包装，避免迭代器工厂被Mono内联后绕过方法后置挂钩。
                yield return new CodeInstruction(OpCodes.Ldarg_0);
                yield return new CodeInstruction(OpCodes.Call, AccessTools.Method(typeof(CreditsHoldSkip), "PreparePlayback"));
                matches++;
            }
        }
        if (matches != 1) throw new InvalidOperationException("CreditsPlayer.Start的PlayCredits调用契约改变");
    }
    public static IEnumerator PreparePlayback(IEnumerator original, MonoBehaviour instance)
    {
        return ObservePreparation(instance, original);
    }
    private static IEnumerator ObservePreparation(MonoBehaviour instance, IEnumerator original)
    {
        bool prepared = false;
        try
        {
            while (original.MoveNext())
            {
                // 原PlayCredits先yield一帧，再格式化并设置正文，随后首次等待预滚动时长。
                // 原协程的每个yield原样传递，不改变名单、音乐或空格快进。
                if (!prepared && original.Current is WaitForSeconds)
                {
                    var skip = instance.GetComponent<CreditsHoldSkip>();
                    if (skip != null) skip.MarkCreditsPrepared();
                    prepared = true;
                }
                yield return original.Current;
            }
        }
        finally
        {
            var disposable = original as IDisposable;
            if (disposable != null) disposable.Dispose();
        }
    }
    public static void AfterStart(MonoBehaviour __instance)
    {
        if (__instance == null || __instance.GetType().FullName != "Elsinore.Ui.CreditsPlayer") return;
        var skip = __instance.GetComponent<CreditsHoldSkip>();
        if (skip == null) skip = __instance.gameObject.AddComponent<CreditsHoldSkip>();
        skip.player = __instance;
        skip.gesture.Reset();
        skip.creditsPrepared = false;
        skip.firstPresentationFrame = -1;
        skip.completionQueued = false;
        try { skip.IgnoreCreditsBody(); }
        catch (Exception error)
        {
            Debug.LogWarning("片尾名单翻译排除失败，保留原文本处理：" + error.GetType().Name);
        }
        try { skip.CreateOverlay(); }
        catch (Exception error)
        {
            skip.enabled = false;
            Debug.LogWarning("片尾跳过提示创建失败，保留原游戏行为：" + error.GetType().Name);
        }
    }
    private void OnDisable()
    {
        Canvas.willRenderCanvases -= ObserveCanvasReady;
        gesture.Reset();
        firstPresentationFrame = -1;
        if (progressRing != null) progressRing.Progress = 0;
        if (overlay != null) overlay.SetActive(false);
    }
    private void OnApplicationFocus(bool focused)
    {
        // 暂停后台更新时也能收到焦点事件，防止切回后把后台时间算作长按。
        if (focused || completionQueued) return;
        gesture.Reset();
        if (progressRing != null) progressRing.Progress = 0;
    }
    private void OnEnable()
    {
        Canvas.willRenderCanvases += ObserveCanvasReady;
        if (overlay != null) overlay.SetActive(true);
    }
    public static bool IsCreditsBody(TMP_Text component) { return creditsBodies.Contains(component); }
    public static bool ContinueStabilization(object __instance, ref bool __result)
    {
        if (creditsBodies.Count == 0 || !IsCreditsBody(stabilizationUi.GetValue(__instance) as TMP_Text)) return true;
        // TMP启用时可能已排队，XUnity旧协程恢复时不会再检查ShouldIgnore。
        // 在真实MoveNext检查，避开Mono内联迭代器工厂的问题；只终止同一正文的延迟任务。
        stabilizationFlag.SetValue(stabilizationInfo.GetValue(__instance), false, null);
        __result = false;
        return false;
    }
    private void IgnoreCreditsBody()
    {
        var field = AccessTools.Field(player.GetType(), "TextField");
        var body = field == null ? null : field.GetValue(player) as TMP_Text;
        var translator = AutoTranslator.Default;
        if (body == null || translator == null) return;
        // 仅排除真实名单正文：保留人员姓名及原格式，避免巨型富文本重复拆分与上下文分配。
        // 提示文字仍走正常离线翻译和F8；不按字数或对象名称泛化排除其它正文。
        translator.IgnoreTextComponent(body);
        creditsBody = body;
        creditsBodies.Add(body);
    }
    private void OnDestroy()
    {
        if (!ReferenceEquals(creditsBody, null))
        {
            creditsBodies.Remove(creditsBody);
            if (creditsBody != null && AutoTranslator.Default != null)
                AutoTranslator.Default.UnignoreTextComponent(creditsBody);
            creditsBody = null;
        }
        if (overlay != null) Destroy(overlay);
    }
    private void CreateOverlay()
    {
        if (overlay != null) { overlay.SetActive(true); return; }
        overlay = new GameObject("ElsinoreHanCreditsSkip", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler));
        // 独立根Canvas保持右下角提示不受片尾静帧遮挡，销毁时由本组件清理。
        var canvas = overlay.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay; canvas.sortingOrder = 32760;
        canvas.enabled = false;
        var scaler = overlay.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight; scaler.matchWidthOrHeight = 0.5f;
        var panel = new GameObject("Hint", typeof(RectTransform)).GetComponent<RectTransform>();
        panel.SetParent(overlay.transform, false);
        panel.anchorMin = panel.anchorMax = new Vector2(1, 0); panel.pivot = new Vector2(1, 0);
        panel.anchoredPosition = new Vector2(-32, 32); panel.sizeDelta = new Vector2(360, 52);
        var label = new GameObject("HintText", typeof(RectTransform), typeof(TextMeshProUGUI)).GetComponent<TextMeshProUGUI>();
        label.rectTransform.SetParent(panel, false);
        label.rectTransform.anchorMin = label.rectTransform.anchorMax = new Vector2(1, 0.5f);
        label.rectTransform.pivot = new Vector2(1, 0.5f);
        label.rectTransform.anchoredPosition = new Vector2(-56, 0); label.rectTransform.sizeDelta = new Vector2(300, 52);
        var textField = AccessTools.Field(player.GetType(), "TextField");
        var template = textField == null ? null : textField.GetValue(player) as TMP_Text;
        if (template != null) label.font = template.font;
        label.fontSize = 24; label.color = Color.white; label.fontStyle = FontStyles.Normal;
        label.alignment = TextAlignmentOptions.MidlineRight; label.enableWordWrapping = false; label.raycastTarget = false;
        label.text = HintSource;
        hintLabel = label;
        CreateRing(panel, "Track", new Color(0.25f, 0.25f, 0.25f, 1), 1);
        progressRing = CreateRing(panel, "Progress", Color.white, 0);
    }
    private void MarkCreditsPrepared()
    {
        creditsPrepared = true;
        if (overlay == null) return;
        overlay.GetComponent<Canvas>().enabled = true;
        hintLabel.ForceMeshUpdate();
        Canvas.ForceUpdateCanvases();
    }
    private void ObserveCanvasReady()
    {
        if (firstPresentationFrame >= 0 || !creditsPrepared || overlay == null || !overlay.activeInHierarchy
            || hintLabel == null || !hintLabel.isActiveAndEnabled || hintLabel.textInfo.characterCount == 0
            || progressRing == null || !progressRing.isActiveAndEnabled || !overlay.GetComponent<Canvas>().enabled) return;
        // Canvas完成布局后再跨过一帧，不能在强制刷新回调内立即开始计时。
        firstPresentationFrame = Time.frameCount;
    }
    public bool PresentationReady
    {
        get { return creditsPrepared && firstPresentationFrame >= 0 && Time.frameCount > firstPresentationFrame; }
    }
    private static CreditsSkipRing CreateRing(RectTransform parent, string name, Color color, float progress)
    {
        var ring = new GameObject(name, typeof(RectTransform), typeof(CreditsSkipRing)).GetComponent<CreditsSkipRing>();
        ring.rectTransform.SetParent(parent, false);
        ring.rectTransform.anchorMin = ring.rectTransform.anchorMax = new Vector2(1, 0.5f);
        ring.rectTransform.pivot = new Vector2(1, 0.5f);
        ring.rectTransform.sizeDelta = new Vector2(36, 36); ring.rectTransform.anchoredPosition = new Vector2(-4, 0);
        ring.color = color; ring.raycastTarget = false; ring.Progress = progress;
        return ring;
    }
    private void Update()
    {
        HandleKey(Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl),
            Application.isFocused, Time.realtimeSinceStartup);
    }
    // 自动验证可调用同一路径；不伪称物理按键验收。
    public bool HandleKey(bool controlHeld, bool focused, double now)
    {
        bool active = player != null && player.isActiveAndEnabled && gameObject.activeInHierarchy;
        if (completionQueued) return false;
        bool complete = gesture.Tick(active, focused, controlHeld, now, PresentationReady);
        if (progressRing != null) progressRing.Progress = gesture.Progress;
        if (!complete) return false;
        completionQueued = true;
        // 原片尾结尾只有Quit与Break，结局标记和保存尝试均发生在加载credits场景前。
        // 仅停止片尾播放器自己的滚动协程；先显示一帧满环，再执行相同退出动作。
        player.StopAllCoroutines();
        StartCoroutine(FinishAfterFullRing());
        return true;
    }
    private IEnumerator FinishAfterFullRing()
    {
        yield return null;
        Application.Quit();
        Debug.Break();
    }
}
