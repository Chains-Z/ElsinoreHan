using System;
using System.Collections;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

// 仅在原CreditsPlayer完成Start后附加；保留原输入、滚动及音乐快进逻辑。
public sealed class CreditsHoldSkip : MonoBehaviour
{
    public const string HintSource = "Hold Ctrl to skip";
    private MonoBehaviour player;
    private GameObject overlay;
    private CreditsSkipRing progressRing;
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
        harmony.Patch(start, postfix: new HarmonyMethod(typeof(CreditsHoldSkip), "AfterStart"));
    }
    public static void AfterStart(MonoBehaviour __instance)
    {
        if (__instance == null || __instance.GetType().FullName != "Elsinore.Ui.CreditsPlayer") return;
        var skip = __instance.GetComponent<CreditsHoldSkip>();
        if (skip == null) skip = __instance.gameObject.AddComponent<CreditsHoldSkip>();
        skip.player = __instance;
        skip.gesture.Reset();
        skip.completionQueued = false;
        try { skip.CreateOverlay(); }
        catch (Exception error)
        {
            skip.enabled = false;
            Debug.LogWarning("片尾跳过提示创建失败，保留原游戏行为：" + error.GetType().Name);
        }
    }
    private void OnDisable()
    {
        gesture.Reset();
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
    private void OnEnable() { if (overlay != null) overlay.SetActive(true); }
    private void OnDestroy() { if (overlay != null) Destroy(overlay); }
    private void CreateOverlay()
    {
        if (overlay != null) { overlay.SetActive(true); return; }
        overlay = new GameObject("ElsinoreHanCreditsSkip", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler));
        // 独立根Canvas保持右下角提示不受片尾静帧遮挡，销毁时由本组件清理。
        var canvas = overlay.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay; canvas.sortingOrder = 32760;
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
        CreateRing(panel, "Track", new Color(0.25f, 0.25f, 0.25f, 1), 1);
        progressRing = CreateRing(panel, "Progress", Color.white, 0);
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
        bool complete = gesture.Tick(active, focused, controlHeld, now);
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
