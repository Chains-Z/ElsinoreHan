using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Reflection;
using BepInEx;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using HarmonyLib;

// 记录真实场景文字与字形覆盖；临时诊断使用隔离存档并阻断保存。
[BepInPlugin("elsinorehan.runtimeprobe", "ElsinoreHan Runtime Probe", "0.1.0")]
public sealed class RuntimeProbe : BaseUnityPlugin
{
    private float started;
    private bool captured;
    private bool openedSettings;
    private bool capturedSettings;
    private bool audioSuspended;
    private string outputDirectory;
    private bool requireToggle;
    private bool showedOriginal;
    private bool restoredTranslated;
    private float nextMenuCheck;
    private float capturedMenuAt;
    private float menuRetryDelay = 1f;
    private bool requestedPause;
    private bool requestedSplash;
    private object pendingPauseAction;
    private object pauseRequestOwner;
    private int pauseRequestAttempts;
    private bool pauseRetryExhausted;
    private string lastMenuAdmission;
    private bool saveGuardActive;
    private bool requireSettingsOptions;
    private bool settingsOptionsFinished;
    private StringBuilder settingsOptionsReport;
    private bool requireJournal;
    private bool journalStarted;
    private bool journalFinished;
    private StringBuilder journalReport;
    private static int blockedSaveWrites;
    private static int blockedPresentationSubmits;
    private static int blockedPhysicalButtons;
    private static bool physicalInputGuardActive;
    private static int disabledPhysicalInputModules;
    private static string isolatedSaveDirectory;
    private bool fontBakeStarted;

    private void Awake()
    {
        started = Time.realtimeSinceStartup;
        var runId = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_RUN_ID");
        Guid parsedRunId;
        if (!Guid.TryParseExact(runId, "N", out parsedRunId))
        {
            Logger.LogError("缺少有效的独立探针运行编号，立即退出。");
            Application.Quit();
            return;
        }
        outputDirectory = Path.Combine(Path.Combine(Paths.GameRootPath, "ElsinoreHanProbe"), runId);
        requireToggle = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_TOGGLE") == "1";
        requireSettingsOptions = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SETTINGS_OPTIONS") == "1";
        requireJournal = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_JOURNAL") == "1";
        string retryDelay = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS");
        if (!string.IsNullOrEmpty(retryDelay))
        {
            float value;
            if (!float.TryParse(retryDelay, System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out value) || float.IsNaN(value) || float.IsInfinity(value) || value < 1f || value > 10f)
            {
                Logger.LogError("菜单重试延迟必须在1到10秒之间，保护建立前直接终止。");
                System.Diagnostics.Process.GetCurrentProcess().Kill();
                return;
            }
            menuRetryDelay = value;
        }
        // 自动探针只允许后台运行；普通游玩不安装此插件。
        if (!Application.isBatchMode)
        {
            Logger.LogError("探针要求 -batchmode；立即退出，禁止常规前台运行。");
            Application.Quit();
            return;
        }
        // 游戏退出和定时器都会保存；测试必须阻断真实保存入口，不能仅避开菜单按钮。
        try
        {
            isolatedSaveDirectory = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH");
            if (string.IsNullOrEmpty(isolatedSaveDirectory) || !Directory.Exists(isolatedSaveDirectory))
                throw new InvalidOperationException("缺少隔离存档副本，禁止继续诊断");
            var saveMethod = typeof(SaveLoad).GetMethod("SaveData", BindingFlags.Public | BindingFlags.Instance);
            var directoryMethod = typeof(SaveLoad).GetProperty("SaveFileDirectory", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance).GetGetMethod(true);
            if (saveMethod == null) throw new InvalidOperationException("未找到保存入口，禁止继续诊断");
            var guard = new Harmony("elsinorehan.runtimeprobe.saveguard");
            guard.Patch(directoryMethod,
                prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("UseIsolatedSaveDirectory", BindingFlags.Public | BindingFlags.Static)));
            guard.Patch(saveMethod,
                prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockSaveWrite", BindingFlags.Public | BindingFlags.Static)));
            guard.Patch(typeof(SaveLoad).GetMethod("MigrateOldSaveFiles", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance),
                prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockSaveMigration", BindingFlags.Public | BindingFlags.Static)));
            var resolutionMethod = typeof(Elsinore.GraphicsPreferenceManager).GetMethod("ApplyQualitySetting", BindingFlags.Public | BindingFlags.Static);
            if (resolutionMethod == null) throw new InvalidOperationException("未找到后台显示配置保护入口");
            guard.Patch(resolutionMethod,
                prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockProbeResolutionChange", BindingFlags.Public | BindingFlags.Static)));
            // Rewired在无窗口后台仍会产生真实按键；只隔离本进程的物理输入。
            // 组件导航继续走EventSystem/真实UiToggle，不把这种验证称为物理键盘E2E。
            foreach (var method in typeof(PlayerInputManaged).GetMethods(InstanceFields))
            {
                if (method.ReturnType == typeof(bool) && method.Name.StartsWith("GetButton", StringComparison.Ordinal))
                    guard.Patch(method, prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockPhysicalButton", BindingFlags.Public | BindingFlags.Static)));
                if (method.ReturnType == typeof(float) && method.Name.StartsWith("GetAxis", StringComparison.Ordinal))
                    guard.Patch(method, prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockPhysicalAxis", BindingFlags.Public | BindingFlags.Static)));
                if (method.ReturnType == typeof(Vector2) && method.Name.StartsWith("GetAxis", StringComparison.Ordinal))
                    guard.Patch(method, prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockPhysicalVector", BindingFlags.Public | BindingFlags.Static)));
            }
            physicalInputGuardActive = true;
            Logger.LogInfo("后台物理输入隔离已启用；不操作用户游戏，不执行物理键盘验收。");
            if (requireJournal)
            {
                var presentation = typeof(SaveLoad).Assembly.GetType("Elsinore.Ui.PresentUI");
                var submit = presentation == null ? null : presentation.GetMethod("presentHearsay", InstanceFields);
                if (submit == null) throw new InvalidOperationException("未找到分享提交保护入口");
                guard.Patch(submit, prefix: new HarmonyMethod(typeof(RuntimeProbe).GetMethod("BlockProbePresentationSubmit", BindingFlags.Public | BindingFlags.Static)));
            }
            saveGuardActive = true;
            Logger.LogInfo("临时诊断存档写入保护已启用：存档目录已隔离，SaveLoad.SaveData全部阻断。");
            Logger.LogInfo("临时后台窗口保护已启用：后台诊断跳过显示质量与分辨率应用。");
        }
        catch (Exception error)
        {
            Logger.LogError("无法建立存档保护，立即终止诊断进程：" + error.GetType().Name);
            // 不能调用Application.Quit，否则未拦截的OnDestroy仍可能保存。
            System.Diagnostics.Process.GetCurrentProcess().Kill();
            return;
        }
        AudioListener.pause = true;
        AudioListener.volume = 0f;
        Application.targetFrameRate = 10;
        Logger.LogInfo("后台模式确认：Application.isBatchMode=True；Unity 音频已暂停。");
        Logger.LogInfo("运行时探针启动；不调用翻译服务，仅使用隔离存档副本。");
    }

    private void Update()
    {
        // 阻断自动输入模块的真实鼠标/提交事件，保留EventSystem的显式组件事件入口。
        foreach (var module in Resources.FindObjectsOfTypeAll<BaseInputModule>())
            if (module.enabled && module.gameObject.scene.IsValid() && module.gameObject.scene.isLoaded)
            {
                module.enabled = false;
                disabledPhysicalInputModules++;
                Logger.LogInfo("已隔离后台自动物理输入模块：" + module.GetType().FullName);
            }
        if (AkSoundEngine.IsInitialized())
        {
            var result = AkSoundEngine.Suspend(true);
            if (!audioSuspended)
            {
                audioSuspended = true;
                Logger.LogInfo("Wwise 后台音频暂停结果=" + result);
            }
        }
        if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_FONT_SOURCE")))
        {
            if (!fontBakeStarted && audioSuspended && Time.realtimeSinceStartup - started > 2f)
            {
                fontBakeStarted = true;
                StartCoroutine(FontBakeProbe.Run(outputDirectory));
            }
            return;
        }
        if ((requireToggle || requireSettingsOptions || requireJournal) && !captured && Time.realtimeSinceStartup - started > 12f
            && Time.realtimeSinceStartup > nextMenuCheck)
        {
            nextMenuCheck = Time.realtimeSinceStartup + 1f;
            CheckStartupNavigation();
        }
        if (!captured && Time.realtimeSinceStartup - started > 18f && MainMenuReady())
        {
            captured = true;
            capturedMenuAt = Time.realtimeSinceStartup;
            Capture("menu");
        }
        float menuAge = captured ? Time.realtimeSinceStartup - capturedMenuAt : -1f;
        if (!openedSettings && menuAge > 2f && (!requireToggle || restoredTranslated))
        {
            foreach (var splash in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
            {
                if (splash == null || splash.GetType().Name != "SplashScreenUI"
                    || !splash.gameObject.scene.IsValid() || !splash.gameObject.scene.isLoaded) continue;
                var field = splash.GetType().GetField("OpenPreferencesButton", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                var button = field == null ? null : field.GetValue(splash) as Component;
                if (button == null || !button.gameObject.activeInHierarchy) continue;
                var pointer = new PointerEventData(EventSystem.current);
                pointer.button = PointerEventData.InputButton.Left;
                EventSystem.current.SetSelectedGameObject(button.gameObject);
                var handled = ExecuteEvents.Execute(button.gameObject, pointer, ExecuteEvents.pointerClickHandler);
                if (!handled) continue;
                openedSettings = true;
                Logger.LogInfo("已通过真实设置按钮的 EventSystem 指针事件打开设置界面。");
                break;
            }
        }
        if (requireToggle && captured && !showedOriginal && menuAge > 1f)
        {
            showedOriginal = true;
            InvokeToggle(false);
            InvokeToggle(true);
            Capture("original-menu");
        }
        if (requireToggle && showedOriginal && !restoredTranslated && menuAge > 1.5f)
        {
            restoredTranslated = true;
            InvokeToggle(true);
            Capture("restored-menu");
        }
        if (openedSettings && !capturedSettings && menuAge > 5f)
        {
            capturedSettings = true;
            Capture("settings");
            if (requireSettingsOptions)
                StartCoroutine(GuardSettingsOptions());
        }
        if (requireJournal && capturedSettings && !journalStarted && menuAge > 6f)
        {
            journalStarted = true;
            StartCoroutine(GuardJournal());
        }
        if ((requireJournal && journalFinished) || Time.realtimeSinceStartup - started > (requireJournal ? 120f : requireSettingsOptions ? 45f : 30f))
        {
            Logger.LogInfo("PROBE_QUIT elapsed=" + (Time.realtimeSinceStartup - started)
                + " journal=" + requireJournal + " finished=" + journalFinished + " menu=" + captured + " settings=" + capturedSettings);
            if (requireSettingsOptions && !settingsOptionsFinished)
                FailSettingsOptions(new TimeoutException("逐档设置验证未在45秒内结束"));
            if (requireJournal && !journalFinished)
                FailJournal(new TimeoutException("真实资料页面采集未在120秒内结束"));
            Application.Quit();
        }
    }

    private const BindingFlags InstanceFields = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

    public static bool BlockPhysicalButton(ref bool __result)
    {
        blockedPhysicalButtons++;
        __result = false;
        return false;
    }

    public static bool BlockPhysicalAxis(ref float __result)
    {
        __result = 0f;
        return false;
    }

    public static bool BlockPhysicalVector(ref Vector2 __result)
    {
        __result = Vector2.zero;
        return false;
    }

    private void CheckStartupNavigation()
    {
        // 跟踪器由场景Awake绑定真实GUI；资源枚举还包含预制件和旧transitioner。
        var tracker = ObjectTracker.Instance;
        var gui = tracker == null ? null : tracker.Gui;
        var boss = tracker == null ? null : tracker.Boss;
        if (gui == null || boss == null || !gui.IsInitialized || !boss.IsGameInitialized) return;
        if ((bool)RequiredProperty(gui, "IsMainMenuActive")) return;
        var overlay = gui.GetType().GetProperty("CurrentlyActiveOverlayCanvas", InstanceFields).GetValue(gui, null);
        var root = gui.GetType().GetProperty("CurrentlyActiveRootCanvas", InstanceFields).GetValue(gui, null);
        var pause = RequiredField(gui, "pauseCanvas");
        bool transitioning = (bool)RequiredProperty(gui, "IsTransitioning");
        bool pauseActive = overlay != null && Equals(overlay, pause);
        var canActivate = gui.GetType().GetMethod("canActivateOverlay", InstanceFields);
        if (canActivate == null) throw new MissingMethodException(gui.GetType().FullName, "canActivateOverlay");
        bool admitted = (bool)canActivate.MakeGenericMethod(pause.GetType()).Invoke(gui, new object[] { pause });
        string admission = "boss=" + boss.GetInstanceID() + " gui=" + gui.GetInstanceID()
            + " initialized=True transitioning=" + transitioning + " canPause=" + admitted
            + " root=" + (root == null ? "null" : root.GetType().Name)
            + " overlay=" + (overlay == null ? "null" : overlay.GetType().Name);
        if (admission != lastMenuAdmission)
        {
            lastMenuAdmission = admission;
            Logger.LogInfo("MENU_NAVIGATION_ADMISSION " + admission);
        }
        if (requestedPause)
        {
            var ownerQueue = RequiredField(pauseRequestOwner, "pendingActions") as IList;
            if (ownerQueue == null) throw new InvalidOperationException("真实暂停请求所属待执行队列不可读");
            if (!ownerQueue.Contains(pendingPauseAction))
            {
                // Boss.Update每帧清空整个队列；准入失败的DeferredAction不会保留到下一帧。
                Logger.LogInfo("MENU_PAUSE_CONSUMED attempt=" + pauseRequestAttempts + " active=" + pauseActive
                    + " transitioning=" + transitioning + " ownerChanged=" + !Equals(pauseRequestOwner, boss));
                requestedPause = false;
                pendingPauseAction = null;
                pauseRequestOwner = null;
                if (!pauseActive) Logger.LogInfo("MENU_PAUSE_RETRY_WAIT attempt=" + pauseRequestAttempts
                    + "；已消费请求未形成Pause，等待真实准入后有限重试。");
            }
            else return;
        }
        var transitions = gui.GetType().GetNestedType("UiTransitions", BindingFlags.Public | BindingFlags.NonPublic);
        var current = Activator.CreateInstance(transitions, InstanceFields, null, new object[] { gui, null }, null);
        if (pauseActive)
        {
            if (!requestedSplash && !transitioning)
            {
                transitions.GetMethod("ActivateSplashScreen").Invoke(current, null);
                requestedSplash = true;
                Logger.LogInfo("真实暂停覆盖层就绪，已一次性展示SplashScreen；不点击新游戏或继续。");
            }
            return;
        }
        if (requestedSplash || transitioning || !admitted || pauseRetryExhausted) return;
        const int maxPauseRequests = 5;
        if (pauseRequestAttempts >= maxPauseRequests)
        {
            pauseRetryExhausted = true;
            Logger.LogError("MENU_PAUSE_RETRY_EXHAUSTED attempts=" + pauseRequestAttempts + "；停止请求，菜单验收保持失败。");
            return;
        }
        var pending = RequiredField(boss, "pendingActions") as IList;
        if (pending == null) throw new InvalidOperationException("真实游戏待执行队列不可读");
        int before = pending.Count;
        // 与真实Esc共用合法暂停动作；不直接激活Canvas或改TimeMode。
        transitions.GetMethod("ActivatePause").Invoke(current, null);
        if (pending.Count != before + 1) throw new InvalidOperationException("真实暂停动作未添加唯一DeferredAction");
        pendingPauseAction = pending[pending.Count - 1];
        pauseRequestOwner = boss;
        requestedPause = true;
        pauseRequestAttempts++;
        Logger.LogInfo("MENU_PAUSE_QUEUED attempt=" + pauseRequestAttempts + " pendingBefore=" + before
            + " pendingAfter=" + pending.Count + " canPause=True；等待真实覆盖层就绪。");
        // 集成回归可延迟消费状态的观察；有限重试仍由真实准入决定。
        nextMenuCheck = Time.realtimeSinceStartup + menuRetryDelay;
        Logger.LogInfo("菜单就绪重试延迟秒数=" + menuRetryDelay);
    }

    private bool MainMenuReady()
    {
        if (!requireToggle && !requireSettingsOptions && !requireJournal) return true;
        var gui = ObjectTracker.Instance.Gui;
        if (gui == null || !gui.IsInitialized) return false;
        var property = gui.GetType().GetProperty("IsMainMenuActive", InstanceFields);
        return property != null && (bool)property.GetValue(gui, null) && !(bool)RequiredProperty(gui, "IsTransitioning");
    }

    private IEnumerator WaitForUiIdle(string phase)
    {
        float deadline = Time.realtimeSinceStartup + 6f;
        var gui = ObjectTracker.Instance.Gui;
        while ((bool)RequiredProperty(gui, "IsTransitioning"))
        {
            if (Time.realtimeSinceStartup > deadline)
                throw new TimeoutException("真实UI转换未结束：" + phase);
            yield return new WaitForSecondsRealtime(0.1f);
        }
        JournalLine("UI_TRANSITION_IDLE\t" + phase + "\tTrue");
    }

    private static object RequiredField(object owner, string name)
    {
        if (owner == null) throw new InvalidOperationException("字段所属对象为空：" + name);
        var field = owner.GetType().GetField(name, InstanceFields);
        if (field == null) throw new MissingFieldException(owner.GetType().FullName, name);
        var value = field.GetValue(owner);
        if (value == null) throw new InvalidOperationException("真实字段未就绪：" + name);
        return value;
    }

    private static object RequiredProperty(object owner, string name)
    {
        if (owner == null) throw new InvalidOperationException("属性所属对象为空：" + name);
        var property = owner.GetType().GetProperty(name, InstanceFields);
        if (property == null) throw new MissingMemberException(owner.GetType().FullName, name);
        var value = property.GetValue(owner, null);
        if (value == null) throw new InvalidOperationException("真实属性未就绪：" + name);
        return value;
    }

    private void SettingsOptionsLine(string line)
    {
        settingsOptionsReport.AppendLine(line);
        Directory.CreateDirectory(outputDirectory);
        File.WriteAllText(Path.Combine(outputDirectory, "settings-options.txt"), settingsOptionsReport.ToString(), new UTF8Encoding(false));
    }

    private static string ReportText(string value)
    {
        return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? ""));
    }

    private static string SourceHash(string value)
    {
        using (var sha = System.Security.Cryptography.SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value))).Replace("-", "").ToLowerInvariant();
    }

    private void JournalLine(string line)
    {
        journalReport.AppendLine(line);
        Directory.CreateDirectory(outputDirectory);
        File.WriteAllText(Path.Combine(outputDirectory, "journal-ui.txt"), journalReport.ToString(), new UTF8Encoding(false));
    }

    private void FailJournal(Exception error)
    {
        if (journalFinished) return;
        journalFinished = true;
        if (journalReport == null) journalReport = new StringBuilder();
        JournalLine("FAILURE\t" + ReportText(error.ToString()));
        JournalLine("STATUS\tFAILED");
        Logger.LogError("真实资料页面诊断失败：" + error);
    }

    // 手动推进嵌套迭代器，让页签、F8和页面转换中的异常都进入同一个失败边界。
    private IEnumerator GuardJournal()
    {
        journalReport = new StringBuilder();
        JournalLine("STATUS\tSTARTED");
        JournalLine("PROBE_SCHEMA\t5");
        JournalLine("SAVE_WRITE_GUARD_ACTIVE\t" + saveGuardActive);
        JournalLine("METHOD\t真实隔离存档页面与组件导航；不宣称像素渲染或完整游玩E2E");
        var routines = new Stack<IEnumerator>();
        routines.Push(ProbeJournal());
        while (routines.Count > 0)
        {
            bool more;
            object current = null;
            try
            {
                more = routines.Peek().MoveNext();
                if (more) current = routines.Peek().Current;
            }
            catch (Exception error)
            {
                FailJournal(error);
                yield break;
            }
            if (!more) { routines.Pop(); continue; }
            var child = current as IEnumerator;
            if (child != null) { routines.Push(child); continue; }
            yield return current;
        }
    }

    private object CurrentTransitions()
    {
        var gui = ObjectTracker.Instance.Gui;
        var active = RequiredProperty(gui, "ActiveModalControl");
        var type = gui.GetType().GetNestedType("UiTransitions", BindingFlags.Public | BindingFlags.NonPublic);
        return Activator.CreateInstance(type, InstanceFields, null, new object[] { gui, active }, null);
    }

    private void JournalTransition(string method, object[] arguments)
    {
        var transitions = CurrentTransitions();
        var entry = transitions.GetType().GetMethod(method, InstanceFields);
        if (entry == null) throw new MissingMethodException("真实页面转换入口缺失：" + method);
        entry.Invoke(transitions, arguments);
        JournalLine("TRANSITION\t" + method);
    }

    private Component JournalCanvas(string field, string phase, bool required = true)
    {
        var gui = ObjectTracker.Instance.Gui;
        var canvas = RequiredField(gui, field) as Component;
        var currentControl = RequiredProperty(gui, "ActiveModalControl");
        var overlayProperty = gui.GetType().GetProperty("CurrentlyActiveOverlayCanvas", InstanceFields);
        var currentOverlay = overlayProperty == null ? null : overlayProperty.GetValue(gui, null);
        var rootProperty = gui.GetType().GetProperty("CurrentlyActiveRootCanvas", InstanceFields);
        var currentRoot = rootProperty == null ? null : rootProperty.GetValue(gui, null);
        bool pausedHudRoot = phase == "hud" && ReferenceEquals(canvas, currentRoot)
            && currentOverlay != null && currentOverlay.GetType().Name == "PauseUI"
            && Convert.ToInt32(RequiredProperty(ObjectTracker.Instance.Info, "TimeMode")) == 2;
        bool belongsToCurrent = field == "logCanvas" ? ReferenceEquals(canvas, currentOverlay)
            : ReferenceEquals(canvas, currentControl) || pausedHudRoot;
        bool active = canvas != null && canvas.gameObject.scene.IsValid() && canvas.gameObject.scene.isLoaded
            && canvas.gameObject.activeInHierarchy && belongsToCurrent;
        JournalLine("NAVIGATION\t" + phase + "\t" + field + "\t" + active);
        JournalLine("NAV_OWNER\t" + phase + "\tmodal=" + ReferenceEquals(canvas, currentControl)
            + "\toverlay=" + ReferenceEquals(canvas, currentOverlay) + "\tpaused_root=" + pausedHudRoot);
        if (!active)
        {
            if (required) throw new InvalidOperationException("真实页面转换未完成：" + phase);
            JournalLine("UNAVAILABLE\t" + phase + "\t真实页面未归属当前合法覆盖层，不能作为通过证据");
            return null;
        }
        return canvas;
    }

    private static string TextPath(Transform transform)
    {
        string path = transform.name;
        while (transform.parent != null)
        {
            transform = transform.parent;
            path = transform.name + "/" + path;
        }
        return path;
    }

    private Dictionary<int, string> JournalSnapshot(string phase, string mode, Component canvas)
    {
        var snapshot = new Dictionary<int, string>();
        int nonempty = 0;
        foreach (var text in canvas.GetComponentsInChildren<TMP_Text>(true))
        {
            if (!text.gameObject.activeInHierarchy) continue;
            string value = text.text ?? "";
            snapshot[text.GetInstanceID()] = value;
            if (value.Length > 0) nonempty++;
            var backing = typeof(TMP_Text).GetField("m_text", InstanceFields);
            string raw = backing == null ? "" : (string)backing.GetValue(text);
            JournalLine("TEXT\t" + phase + "\t" + mode + "\t" + text.GetInstanceID()
                + "\t" + ReportText(TextPath(text.transform)) + "\t" + ReportText(value)
                + "\t" + text.isTextOverflowing + "\t" + ReportText(raw));
            if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_TYPOGRAPHY") == "1")
            {
                text.ForceMeshUpdate();
                var parentCanvas = text.GetComponentInParent<Canvas>();
                JournalLine("TYPOGRAPHY\t" + phase + "\t" + mode + "\t" + text.GetInstanceID()
                    + "\t" + text.fontSize + "\t" + text.enableAutoSizing
                    + "\t" + (text.font == null ? "" : text.font.name)
                    + "\t" + text.transform.lossyScale.x + "\t" + text.transform.lossyScale.y
                    + "\t" + (parentCanvas == null ? 0f : parentCanvas.scaleFactor));
                bool latin = false, han = false;
                for (int characterIndex = 0; characterIndex < text.textInfo.characterCount; characterIndex++)
                {
                    var character = text.textInfo.characterInfo[characterIndex];
                    if (!character.isVisible || character.fontAsset == null) continue;
                    bool isLatin = (character.character >= 'A' && character.character <= 'Z')
                        || (character.character >= 'a' && character.character <= 'z');
                    bool isHan = character.character >= '\u4e00' && character.character <= '\u9fff';
                    if ((!isLatin || latin) && (!isHan || han)) continue;
                    latin |= isLatin; han |= isHan;
                    JournalLine("TYPOGRAPHY_GLYPH\t" + phase + "\t" + mode + "\t" + text.GetInstanceID()
                        + "\t" + (int)character.character + "\t" + character.fontAsset.name
                        + "\t" + character.pointSize + "\t" + character.scale
                        + "\t" + character.ascender + "\t" + character.descender
                        + "\t" + (character.topRight.x - character.bottomLeft.x)
                        + "\t" + (character.topRight.y - character.bottomLeft.y));
                    if (latin && han) break;
                }
            }
        }
        JournalLine("CONTENT\t" + phase + "\t" + mode + "\t" + snapshot.Count + "\t" + nonempty);
        if (snapshot.Count == 0) throw new InvalidOperationException("真实页面没有激活的TMP组件：" + phase);
        return snapshot;
    }

    private void JournalLookup(string phase, string key, string source, string displayed)
    {
        Type api = null;
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            api = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.AutoTranslator", false);
            if (api != null) break;
        }
        if (api == null) throw new InvalidOperationException("真实翻译缓存API不存在");
        var instance = api.GetProperty("Default").GetValue(null, null);
        var contract = api.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.ITranslator");
        var lookup = contract.GetMethod("TryTranslate", new Type[] { typeof(string), typeof(string).MakeByRefType() });
        var arguments = new object[] { source, null };
        bool found = source.Length > 0 && (bool)lookup.Invoke(instance, arguments);
        string translated = arguments[1] as string;
        JournalLine("API\t" + phase + "\t" + key + "\t" + ReportText(source) + "\t" + found
            + "\t" + ReportText(translated) + "\t" + ReportText(displayed)
            + "\t" + (found && translated == displayed));
    }

    private void JournalBuilder(string phase, object owner, string textField)
    {
        var field = owner.GetType().GetField("builder", InstanceFields);
        var builder = field == null ? null : field.GetValue(owner) as StringBuilder;
        if (builder == null) return;
        var displayField = owner.GetType().GetField(textField, InstanceFields);
        var display = displayField == null ? null : displayField.GetValue(owner) as TMP_Text;
        // Hearsay 将 builder 写入各条目，父页签没有 DescriptionText；不与空控件比较。
        if (display == null || !display.gameObject.activeInHierarchy) return;
        JournalLine("BUILDER\t" + phase + "\t" + ReportText(builder.ToString()));
        JournalLookup(phase, "builder:" + textField, builder.ToString(), display.text ?? "");
    }

    private void JournalControl(string phase, string role, object owner, string field)
    {
        var text = RequiredField(owner, field) as TMP_Text;
        if (text == null) throw new InvalidOperationException("真实正文控件类型不兼容：" + role);
        JournalLine("CONTROL\t" + phase + "\t" + role + "\t" + text.GetInstanceID()
            + "\t" + ReportText(TextPath(text.transform)) + "\t" + text.gameObject.activeInHierarchy);
    }

    private IEnumerator JournalRoundTrip(string phase, Component canvas, string[] history = null, IList logEntries = null)
    {
        string clockBefore = JournalClock(phase, "before");
        SetSettingsTranslatedMode(true);
        yield return new WaitForSecondsRealtime(0.35f);
        var translated = JournalSnapshot(phase, "translated", canvas);
        SetSettingsTranslatedMode(false);
        yield return new WaitForSecondsRealtime(0.35f);
        var original = JournalSnapshot(phase, "original", canvas);
        foreach (var item in original)
        {
            string initial;
            translated.TryGetValue(item.Key, out initial);
            JournalLookup(phase, item.Key.ToString(), item.Value, initial ?? "");
        }
        SetSettingsTranslatedMode(true);
        yield return new WaitForSecondsRealtime(0.35f);
        var restored = JournalSnapshot(phase, "restored", canvas);
        foreach (var item in original)
        {
            string initial;
            string after;
            translated.TryGetValue(item.Key, out initial);
            restored.TryGetValue(item.Key, out after);
            JournalLine("ROUNDTRIP\t" + phase + "\t" + item.Key + "\t" + ReportText(item.Value)
                + "\t" + ReportText(initial) + "\t" + ReportText(after)
                + "\t" + (initial != null && after != null && initial == after));
        }
        if (history != null && logEntries != null)
        {
            for (int index = 0; index < history.Length; index++)
            {
                var text = index < logEntries.Count ? logEntries[index] as TMP_Text : null;
                string source = history[index] ?? "";
                string before = null;
                string english = null;
                string after = null;
                int id = text == null ? 0 : text.GetInstanceID();
                translated.TryGetValue(id, out before);
                original.TryGetValue(id, out english);
                restored.TryGetValue(id, out after);
                JournalLine("LOG_ROUNDTRIP\t" + index + "\t" + id + "\t" + ReportText(source)
                    + "\t" + ReportText(english) + "\t" + ReportText(before) + "\t" + ReportText(after)
                    + "\t" + (english != null && english == source)
                    + "\t" + (before != null && after != null && before == after));
            }
        }
        string clockAfter = JournalClock(phase, "after");
        if (clockBefore != clockAfter)
            JournalLine("UNAVAILABLE\t" + phase + ".clock\t真实暂停态采集期间时钟变化，本阶段不能认定F8稳定通过");
    }

    private string JournalClock(string phase, string moment)
    {
        var info = ObjectTracker.Instance.Info;
        int mode = Convert.ToInt32(RequiredProperty(info, "TimeMode"));
        var clock = RequiredProperty(info, "VisibleTime");
        var minutes = clock.GetType().GetProperty("MinutesFromEpochFloat", InstanceFields);
        string value = minutes == null ? (string)RequiredProperty(clock, "AsStringWithDayOfWeek")
            : Convert.ToString(minutes.GetValue(clock, null), System.Globalization.CultureInfo.InvariantCulture);
        JournalLine("CLOCK\t" + phase + "\t" + moment + "\t" + mode + "\t" + ReportText(value));
        if (mode != 2) throw new InvalidOperationException("真实页面未进入游戏暂停态：" + phase);
        return value;
    }

    private void JournalPrefixCounts(string phase, string moment)
    {
        bool found = false;
        foreach (var component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
        {
            if (component == null || component.GetType().Name != "TranslationToggle") continue;
            foreach (var field in component.GetType().GetFields(InstanceFields | BindingFlags.Static))
            {
                if ((field.FieldType != typeof(int) && field.FieldType != typeof(long))
                    || field.Name.IndexOf("prefix", StringComparison.OrdinalIgnoreCase) < 0) continue;
                found = true;
                JournalLine("PREFIX_COUNT\t" + phase + "\t" + moment + "\t" + field.Name
                    + "\t" + Convert.ToString(field.GetValue(field.IsStatic ? null : component), System.Globalization.CultureInfo.InvariantCulture));
            }
        }
        if (!found) JournalLine("PREFIX_COUNTER_UNAVAILABLE\t" + phase + "\t" + moment);
    }

    // 缺失真实业务数据属于未覆盖；继续其它独立页面，不让可选页面阻断文档故障采集。
    private IEnumerator OptionalJournalPhase(string phase, IEnumerator routine)
    {
        var routines = new Stack<IEnumerator>();
        routines.Push(routine);
        while (routines.Count > 0)
        {
            bool more;
            object current = null;
            try
            {
                more = routines.Peek().MoveNext();
                if (more) current = routines.Peek().Current;
            }
            catch (Exception error)
            {
                JournalLine("UNAVAILABLE\t" + phase + "\t" + ReportText(error.ToString()));
                yield break;
            }
            if (!more) { routines.Pop(); continue; }
            var child = current as IEnumerator;
            if (child != null) { routines.Push(child); continue; }
            yield return current;
        }
    }

    private IEnumerator ProbeJournal()
    {
        if (!saveGuardActive || requireSettingsOptions)
            throw new InvalidOperationException("资料页面诊断要求隔离保护且不能与逐档设置模式同时运行");
        var gui = ObjectTracker.Instance.Gui;
        var preferences = RequiredField(gui, "preferencesCanvas") as Component;
        if (preferences != null && preferences.gameObject.activeInHierarchy)
        {
            JournalTransition("CloseSelf", null);
            yield return new WaitForSecondsRealtime(0.4f);
        }
        // 文档故障优先采集，每一页独立失败；不再让其它页面的不可交互按钮截断它们。
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BOOK_ONLY") != "1")
        {
            foreach (string closeupId in new string[] { "observable_hamletdiary", "observable_poldesk", "observable_backerbook4" })
                yield return OptionalJournalPhase(closeupId, ProbeDocument(closeupId));
            yield return OptionalJournalPhase("closeups.batch", ProbeCloseupBatch());
        }
        yield return OptionalJournalPhase("hud", ProbeHud());
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BOOK_PAGES") != null)
        {
            yield return WaitForUiIdle("book:before");
            JournalTransition("ActivateBook", null);
            yield return new WaitForSecondsRealtime(0.6f);
            yield return WaitForUiIdle("book:after");
            yield return EndingBookProbe.Capture(JournalCanvas("endingSelectCanvas", "book"), outputDirectory);
            yield return WaitForUiIdle("confirmation:before");
            var gameOver = (Component)RequiredField(gui, "gameOverCanvas");
            var transitions = CurrentTransitions();
            var activateGameOver = transitions.GetType().GetMethod("ActivateGameOver", InstanceFields);
            Type endingType = Nullable.GetUnderlyingType(activateGameOver.GetParameters()[0].ParameterType);
            // 使用真实已解锁的疯人院结局，不解锁其它结局，也不按下选择或重启按钮。
            object endingId = Activator.CreateInstance(endingType, new object[] { "END_Delusion" });
            activateGameOver.Invoke(transitions, new object[] { endingId, "I tried. I tried to tell them. But they wouldn't believe me.",
                RequiredField(gameOver, "nextMode") });
            yield return new WaitForSecondsRealtime(1.2f);
            yield return WaitForUiIdle("confirmation:after");
            yield return EndingBookProbe.CaptureConfirmation(JournalCanvas("gameOverCanvas", "confirmation"), outputDirectory);
        }
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BOOK_ONLY") == "1")
        {
            JournalLine("STATUS\tCOLLECTED");
            journalFinished = true;
            yield break;
        }
        yield return OptionalJournalPhase("journal", ProbeJournalTabs());
        yield return OptionalJournalPhase("present", ProbePresentationPreview());
        yield return OptionalJournalPhase("timeline", ProbeTimeline());
        yield return OptionalJournalPhase("log", ProbeLog());
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_UI_FOLLOWUP") == "1")
            yield return OptionalJournalPhase("map.followup", MapFollowupProbe.Capture(outputDirectory));
        JournalLine("STATUS\tCOLLECTED");
        journalFinished = true;
        Logger.LogInfo("真实资料页面与SetText局部组件证据已采集；未覆盖阶段不能由COLLECTED推定通过。");
    }

    private IEnumerator ProbeDocument(string closeupId)
    {
        yield return WaitForUiIdle(closeupId + ":before");
        var transitions = CurrentTransitions();
        var activate = transitions.GetType().GetMethod("ActivateObjectCloseup", InstanceFields);
        var id = Activator.CreateInstance(activate.GetParameters()[0].ParameterType, new object[] { closeupId });
        var state = RequiredProperty(ObjectTracker.Instance.Info, "State");
        var lookup = RequiredProperty(state, "Lookup");
        var closeup = lookup.GetType().GetMethod("Closeup").Invoke(lookup, new object[] { id });
        string source = (string)RequiredProperty(closeup, "Text");
        // 真实ObjectCloseupUI.OnClosed无条件调用onDone；探针也必须履行回调契约。
        activate.Invoke(transitions, new object[] { id, new Action(delegate { JournalLine("CLOSEUP_CLOSED\t" + closeupId); }) });
        yield return new WaitForSecondsRealtime(0.4f);
        yield return WaitForUiIdle(closeupId + ":after");
        var document = JournalCanvas("objectCloseupCanvas", closeupId);
        var body = (TMP_Text)RequiredField(document, "Body");
        JournalControl(closeupId, "document.body", document, "Body");
        JournalLine("DOCUMENT_SOURCE\t" + closeupId + "\t" + ReportText(source));
        JournalLookup(closeupId, "resource_body", source, body.text ?? "");
        JournalBuilder(closeupId, document, "Body");
        yield return JournalRoundTrip(closeupId, document);
        // 同一Body与真实资源原文做三种入口对照；不是游戏世界寻物点击E2E。
        JournalPrefixCounts(closeupId, "builder_before");
        body.SetText(new StringBuilder(source));
        yield return new WaitForSecondsRealtime(0.35f);
        JournalPrefixCounts(closeupId, "builder_after");
        JournalLine("COMPONENT_STRINGBUILDER_REAL_SOURCE\t" + closeupId + "\t" + ReportText(source)
            + "\t" + ReportText(body.text) + "\t" + body.isTextOverflowing);
        JournalLookup(closeupId, "component_stringbuilder", source, body.text ?? "");
        JournalPrefixCounts(closeupId, "string_bool_before");
        body.SetText(source, true);
        yield return new WaitForSecondsRealtime(0.35f);
        JournalPrefixCounts(closeupId, "string_bool_after");
        JournalLine("COMPONENT_STRING_BOOL_REAL_SOURCE\t" + closeupId + "\t" + ReportText(source)
            + "\t" + ReportText(body.text) + "\t" + body.isTextOverflowing);
        JournalLookup(closeupId, "component_string_bool", source, body.text ?? "");
        JournalPrefixCounts(closeupId, "string_before");
        body.SetText(source);
        yield return new WaitForSecondsRealtime(0.35f);
        JournalPrefixCounts(closeupId, "string_after");
        JournalLine("COMPONENT_STRING_REAL_SOURCE\t" + closeupId + "\t" + ReportText(source)
            + "\t" + ReportText(body.text) + "\t" + body.isTextOverflowing);
        JournalLookup(closeupId, "component_string", source, body.text ?? "");
    }

    private IEnumerator ProbeHud()
    {
        yield return WaitForUiIdle("hud:before");
        var gui = ObjectTracker.Instance.Gui;
        // 合法内部导航恢复HUD，再打开真实Pause覆盖层，由游戏自动进入TimeMode=2。
        gui.GetType().GetMethod("ActivateExploration", InstanceFields).Invoke(gui, new object[] { false });
        yield return new WaitForSecondsRealtime(0.35f);
        yield return WaitForUiIdle("hud:exploration");
        JournalTransition("ActivatePause", null);
        yield return new WaitForSecondsRealtime(0.4f);
        yield return WaitForUiIdle("hud:paused");
        var hud = JournalCanvas("mainCanvas", "hud");
        JournalControl("hud", "hud.time", hud, "TimeText");
        JournalControl("hud", "hud.room", hud, "LocationText");
        yield return JournalRoundTrip("hud", hud);
    }

    private IEnumerator ProbeJournalTabs()
    {
        yield return WaitForUiIdle("journal:before");
        JournalTransition("ActivateJournal", null);
        yield return new WaitForSecondsRealtime(0.5f);
        yield return WaitForUiIdle("journal:after");
        var journal = JournalCanvas("journalCanvas", "journal");
        string[] toggles = { "CharactersToggle", "HearsayToggle", "LeadsToggle" };
        string[] tabs = { "CharactersTab", "HearsayTab", "LeadsTab" };
        for (int index = 0; index < tabs.Length; index++)
        {
            var toggle = RequiredField(journal, toggles[index]);
            toggle.GetType().GetProperty("IsOn", InstanceFields).SetValue(toggle, true, null);
            yield return new WaitForSecondsRealtime(0.4f);
            var tab = RequiredField(journal, tabs[index]) as Component;
            if (tab == null || !tab.gameObject.activeInHierarchy)
                throw new InvalidOperationException("真实Journal页签没有激活：" + tabs[index]);
            JournalLine("TAB\t" + tabs[index] + "\t" + RequiredProperty(journal, "CurrentTabIndex"));
            if (index == 0)
            {
                JournalControl(tabs[index], "characters.name", tab, "TitleText");
                JournalControl(tabs[index], "characters.body", tab, "DescriptionText");
            }
            else if (index == 2)
            {
                JournalControl(tabs[index], "leads.title", tab, "TitleText");
                JournalControl(tabs[index], "leads.body", tab, "DescriptionText");
                if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_UI_FOLLOWUP") == "1")
                    yield return LeadFollowupProbe.Capture(tab, outputDirectory, new Action<bool>(SetSettingsTranslatedMode));
                if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_LEAD_LAYOUT") == "1")
                    yield return LeadLayoutProbe.Capture(tab, outputDirectory, new Action<bool>(SetSettingsTranslatedMode));
            }
            else
            {
                bool hasEntry = false;
                foreach (var entry in tab.GetComponentsInChildren<MonoBehaviour>(true))
                {
                    if (entry.GetType().Name != "TitleAndDescriptionContainer" || !entry.gameObject.activeInHierarchy) continue;
                    JournalControl(tabs[index], "rumors.title", entry, "title");
                    JournalControl(tabs[index], "rumors.body", entry, "description");
                    hasEntry = true;
                    break;
                }
                if (!hasEntry) JournalLine("UNAVAILABLE\trumors.body\t真实隔离存档当前分类没有已获得的传闻正文");
            }
            JournalBuilder(tabs[index], tab, "DescriptionText");
            yield return JournalRoundTrip(tabs[index], tab);
            if (index == 0)
                yield return OptionalJournalPhase("characters.layout", ProbeCharacterLayout(tab));
        }
    }

    private IEnumerator ProbeCloseupBatch()
    {
        string path = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_CLOSEUP_IDS");
        if (string.IsNullOrEmpty(path) || !File.Exists(path))
            throw new InvalidOperationException("缺少从真实资源生成的冻结Closeup ID文件");
        string digest;
        using (var sha = System.Security.Cryptography.SHA256.Create())
            digest = BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
        JournalLine("CLOSEUP_IDS_FILE_SHA256\t" + digest);
        var ids = new List<string>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (string line in File.ReadAllLines(path, Encoding.UTF8))
        {
            string id = line.Split('\t')[0].Trim();
            if (id.Length == 0) continue;
            if (!id.StartsWith("observable_", StringComparison.Ordinal) || !seen.Add(id))
                throw new InvalidOperationException("冻结资料ID重复或格式异常");
            ids.Add(id);
        }
        JournalLine("CLOSEUP_BATCH_EXPECTED_COUNT\t" + ids.Count);
        foreach (string closeupId in ids)
        {
            yield return WaitForUiIdle("batch:" + closeupId + ":before");
            var transitions = CurrentTransitions();
            var activate = transitions.GetType().GetMethod("ActivateObjectCloseup", InstanceFields);
            var id = Activator.CreateInstance(activate.GetParameters()[0].ParameterType, new object[] { closeupId });
            var lookup = RequiredProperty(RequiredProperty(ObjectTracker.Instance.Info, "State"), "Lookup");
            var closeup = lookup.GetType().GetMethod("Closeup").Invoke(lookup, new object[] { id });
            string source = (string)RequiredProperty(closeup, "Text");
            string callbackId = closeupId;
            activate.Invoke(transitions, new object[] { id, new Action(delegate { JournalLine("CLOSEUP_CLOSED\t" + callbackId); }) });
            yield return new WaitForSecondsRealtime(0.3f);
            yield return WaitForUiIdle("batch:" + closeupId + ":after");
            var document = JournalCanvas("objectCloseupCanvas", "batch:" + closeupId);
            var body = (TMP_Text)RequiredField(document, "Body");
            string combined = ((StringBuilder)RequiredField(document, "builder")).ToString();
            JournalLine("CLOSEUP_BATCH\t" + closeupId + "\t" + ReportText(source) + "\t" + ReportText(combined)
                + "\t" + ReportText(body.text) + "\t" + body.isTextOverflowing);
            JournalLookup("batch:" + closeupId, "builder:Body", combined, body.text ?? "");
            string scrollIds = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS");
            if (!string.IsNullOrEmpty(scrollIds) && Array.IndexOf(scrollIds.Split(';'), closeupId) >= 0)
                yield return DocumentScrollAnchorProbe.Capture(document, closeupId, outputDirectory);
        }
    }

    private static string Metric(float value)
    {
        return value.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
    }

    private static Rect WorldTextBounds(TMP_Text text)
    {
        var local = text.textBounds;
        var first = text.rectTransform.TransformPoint(new Vector3(local.min.x, local.min.y, 0));
        var second = text.rectTransform.TransformPoint(new Vector3(local.max.x, local.max.y, 0));
        return Rect.MinMaxRect(Mathf.Min(first.x, second.x), Mathf.Min(first.y, second.y),
            Mathf.Max(first.x, second.x), Mathf.Max(first.y, second.y));
    }

    private void RecordCharacterGeometry(string character, string role, TMP_Text text)
    {
        text.ForceMeshUpdate();
        var box = WorldTextBounds(text);
        var rect = text.rectTransform.rect;
        JournalLine("CHARACTER_GEOMETRY\t" + character + "\t" + role + "\t" + ReportText(text.text)
            + "\t" + text.textInfo.lineCount + "\t" + Metric(text.fontSize) + "\t" + Metric(rect.width)
            + "\t" + Metric(rect.height) + "\t" + Metric(box.xMin) + "\t" + Metric(box.yMin)
            + "\t" + Metric(box.width) + "\t" + Metric(box.height) + "\t" + text.isTextOverflowing);
    }

    private IEnumerator ProbeCharacterLayout(Component tab)
    {
        var group = RequiredField(tab, "CharacterButtonGroup") as Component;
        var portraits = new List<MonoBehaviour>();
        foreach (var component in group.GetComponentsInChildren<MonoBehaviour>(true))
            if (component.GetType().Name == "CharacterPortrait" && component.gameObject.activeInHierarchy)
                portraits.Add(component);
        JournalLine("CHARACTER_LAYOUT_EXPECTED_COUNT\t" + portraits.Count);
        foreach (var portrait in portraits)
        {
            var button = portrait.GetComponent<Selectable>();
            if (button == null || !button.interactable)
            {
                JournalLine("UNAVAILABLE\tcharacters.layout\t实际人物按钮不可交互");
                continue;
            }
            string character = (string)RequiredProperty(RequiredProperty(portrait, "Character"), "Name");
            ClickSettingsButton(button);
            yield return new WaitForSecondsRealtime(0.3f);
            var title = (TMP_Text)RequiredField(tab, "TitleText");
            var slug = (TMP_Text)RequiredField(tab, "SlugText");
            RecordCharacterGeometry(character, "title", title);
            RecordCharacterGeometry(character, "subtitle", slug);
            JournalBuilder("character:" + character, tab, "DescriptionText");
            if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BIO_SCROLL") == "1")
                yield return BiographyScrollProbe.Capture(tab, character, outputDirectory);
            if (character == "hamlet")
            {
                JournalControl("character:" + character, "character.profile.body", tab, "DescriptionText");
                yield return JournalRoundTrip("character:" + character, tab);
            }
            if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BIOGRAPHY_CASES")))
            {
                JournalControl("character:" + character, "character.profile.body", tab, "DescriptionText");
                yield return BiographyReplayProbe.Capture(tab, character, outputDirectory);
            }
            var a = WorldTextBounds(title);
            var b = WorldTextBounds(slug);
            bool overlaps = a.width > 0 && a.height > 0 && b.width > 0 && b.height > 0
                && Mathf.Min(a.xMax, b.xMax) - Mathf.Max(a.xMin, b.xMin) > 0.5f
                && Mathf.Min(a.yMax, b.yMax) - Mathf.Max(a.yMin, b.yMin) > 0.5f;
            JournalLine("CHARACTER_LAYOUT\t" + character + "\t" + overlaps);
        }
        if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BIOGRAPHY_CASES")))
            BiographyReplayProbe.Complete(outputDirectory);
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_BIO_SCROLL") == "1") BiographyScrollProbe.Complete();
    }

    private IEnumerator ProbePresentationPreview()
    {
        yield return WaitForUiIdle("present:before");
        var tracker = ObjectTracker.Instance;
        var targets = tracker.GetType().GetMethod("AllNpcs", InstanceFields).Invoke(tracker, null) as IEnumerable;
        object target = null;
        foreach (var candidate in targets)
            if (candidate != null) { target = candidate; break; }
        if (target == null) throw new InvalidOperationException("真实场景没有分享预览目标人物");
        JournalTransition("ActivatePresentation", new object[] { target });
        yield return new WaitForSecondsRealtime(0.4f);
        yield return WaitForUiIdle("present:after");
        var present = JournalCanvas("presentCanvas", "present");
        var categories = RequiredField(present, "categoryToggles") as IList;
        var categoryCopies = new List<object>();
        foreach (var category in categories) categoryCopies.Add(category);
        float stop = Time.realtimeSinceStartup + 6f;
        foreach (var category in categoryCopies)
        {
            category.GetType().GetProperty("IsOn", InstanceFields).SetValue(category, true, null);
            yield return new WaitForSecondsRealtime(0.1f);
            var hearsays = RequiredField(present, "hearsayToggles") as IList;
            var copies = new List<object>();
            foreach (var hearsay in hearsays) copies.Add(hearsay);
            foreach (var hearsay in copies)
            {
                if (Time.realtimeSinceStartup > stop) break;
                var selectable = hearsay as Selectable;
                if (selectable == null || !selectable.gameObject.activeInHierarchy || !selectable.interactable) continue;
                var current = present.GetType().GetField("selectedHearsay", InstanceFields).GetValue(present);
                if (ReferenceEquals(current, hearsay)) continue;
                // 首次选择由OnValueChange生成预览；PressedEvent仅在已选项上注册二次提交。
                // 沿用真实UiToggle状态机，不调用提交事件或PresentButton。
                hearsay.GetType().GetProperty("IsOn", InstanceFields).SetValue(hearsay, true, null);
                string source = ((StringBuilder)RequiredField(present, "builder")).ToString();
                JournalLine("PRESENT_PREVIEW_CANDIDATE\t" + ReportText(source));
                // 消费当前已获得且可分享信息的真实首句，不要求存档仍保留指定危险信息。
                if (source.Length < 3 || source[0] != '"' || source[source.Length - 1] != '"') continue;
                string selectedCategory = (string)RequiredField(present, "selectedCategory");
                if ((bool)present.GetType().GetMethod("IsPlayCategory", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static)
                    .Invoke(null, new object[] { selectedCategory })) continue;
                var information = RequiredField(present, "selectedInformation");
                var informationId = RequiredProperty(information, "Id");
                var targetId = RequiredProperty(target, "Id");
                var sceneId = information.GetType().GetMethod("SceneOf", InstanceFields).Invoke(information, new object[] { targetId });
                string firstLine = source.Substring(1, source.Length - 2);
                yield return new WaitForSecondsRealtime(0.3f);
                var preview = (TMP_Text)RequiredField(present, "PresentPreviewText");
                JournalControl("present", "present.preview", present, "PresentPreviewText");
                JournalLine("PRESENT_PREVIEW_SOURCE\t" + ReportText(source));
                JournalLine("PRESENT_PREVIEW_ORIGIN\t" + ReportText((string)RequiredProperty(informationId, "Name"))
                    + "\t" + ReportText((string)RequiredProperty(targetId, "Name"))
                    + "\t" + ReportText((string)RequiredProperty(sceneId, "Name"))
                    + "\t" + ReportText(firstLine) + "\t" + SourceHash(firstLine) + "\t" + SourceHash(source));
                JournalLine("PRESENT_SUBMIT_BLOCKED_COUNT\t" + blockedPresentationSubmits);
                JournalLookup("present", "builder:PresentPreviewText", source, preview.text ?? "");
                yield return JournalRoundTrip("present", present);
                yield break;
            }
            if (Time.realtimeSinceStartup > stop) break;
        }
        throw new InvalidOperationException("当前真实已获得信息没有非空可分享首句；没有虚构资料补齐");
    }

    private IEnumerator ProbeTimeline()
    {
        yield return WaitForUiIdle("timeline:before");
        JournalTransition("ActivateTimeline", null);
        yield return new WaitForSecondsRealtime(0.5f);
        yield return WaitForUiIdle("timeline:after");
        var timeline = JournalCanvas("timelineCanvas", "timeline");
        float waitUntil = Time.realtimeSinceStartup + 4f;
        while ((bool)RequiredField(timeline, "isLoading") && Time.realtimeSinceStartup < waitUntil)
            yield return new WaitForSecondsRealtime(0.2f);
        if ((bool)RequiredField(timeline, "isLoading"))
        {
            JournalLine("UNAVAILABLE\ttimeline\t真实时间线仍未完成计算");
            yield break;
        }
        var items = RequiredField(timeline, "currentItems") as IEnumerable;
        object selected = null;
        if (items != null)
            foreach (var item in items)
            {
                var button = RequiredField(item, "Item2") as Selectable;
                if (button != null && button.gameObject.activeInHierarchy && button.interactable)
                { selected = button; break; }
            }
        if (selected == null)
        {
            JournalLine("UNAVAILABLE\ttimeline_detail\t真实隔离存档时间线没有可点击事件");
        }
        else
        {
            var component = (Component)selected;
            ExecuteEvents.Execute(component.gameObject, new PointerEventData(EventSystem.current), ExecuteEvents.pointerEnterHandler);
            ClickSettingsButton(selected);
            yield return new WaitForSecondsRealtime(0.4f);
            JournalControl("timeline", "timeline.detail", timeline, "InfoText");
            JournalBuilder("timeline_detail", timeline, "InfoText");
        }
        yield return JournalRoundTrip("timeline", timeline);
        if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_UI_FOLLOWUP") == "1")
            yield return TimelineFollowupProbe.Capture(outputDirectory, new Action<bool>(SetSettingsTranslatedMode));
        var deactivate = timeline.GetType().GetMethod("DeactivateEventInfoPopup", InstanceFields);
        if (deactivate != null) deactivate.Invoke(timeline, null);
    }

    private IEnumerator ProbeLog()
    {
        yield return WaitForUiIdle("log:before");
        var gui = ObjectTracker.Instance.Gui;
        // 这是受隔离保护的组件导航；不强求可能被教程禁用的物理关闭按钮。
        gui.GetType().GetMethod("ActivateExploration", InstanceFields).Invoke(gui, new object[] { false });
        yield return new WaitForSecondsRealtime(0.35f);
        yield return WaitForUiIdle("log:exploration");
        var logOrigin = JournalCanvas("mainCanvas", "log_origin_hud", false);
        // 日志覆盖层只能从真正允许日志的HUD/对白或主菜单进入，不能从Timeline强开。
        if (logOrigin == null || !(bool)RequiredProperty(logOrigin, "IsLogButtonActive"))
            JournalLine("UNAVAILABLE\tlog.entry\t真实HUD日志按钮未开放或没有运行历史");
        else
        {
            JournalTransition("ActivateLog", null);
            yield return new WaitForSecondsRealtime(0.5f);
            yield return WaitForUiIdle("log:after");
            var log = JournalCanvas("logCanvas", "log", false);
            if (log != null)
            {
                if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_ITALIC") == "1"
                    && !ItalicGeometryProbe.TryCapture(outputDirectory))
                    throw new InvalidOperationException("未取得对白与日志的真实字体几何，不能宣称斜体修复通过");
                var history = RequiredProperty(RequiredField(log, "ht"), "HistoryText") as string[];
                var logEntries = RequiredField(log, "createdEntries") as IList;
                JournalLine("HISTORY_COUNT\t" + (history == null ? 0 : history.Length));
                JournalLine("LOG_ENTRIES_COUNT\t" + (logEntries == null ? 0 : logEntries.Count));
                if (history == null || history.Length == 0 || logEntries == null)
                    JournalLine("UNAVAILABLE\tlog.entry\t真实运行历史没有可验证的日志正文");
                else
                {
                    // 原游戏按同一index将HistoryText[index]写入createdEntries[index]，不能仅验第一条。
                    for (int index = 0; index < history.Length; index++)
                        JournalLine("HISTORY_SOURCE\t" + index + "\t" + ReportText(history[index]));
                    for (int index = 0; index < logEntries.Count; index++)
                    {
                        var text = logEntries[index] as TMP_Text;
                        string source = index < history.Length ? history[index] ?? "" : "";
                        bool active = text != null && text.gameObject.activeInHierarchy;
                        JournalLine("LOG_ENTRY\t" + index + "\t" + (text == null ? 0 : text.GetInstanceID())
                            + "\t" + ReportText(text == null ? "" : TextPath(text.transform))
                            + "\t" + ReportText(source) + "\t" + active + "\t" + ReportText(text == null ? "" : text.text));
                        if (!active) continue;
                        JournalLine("CONTROL\tlog\tlog.entry\t" + text.GetInstanceID()
                            + "\t" + ReportText(TextPath(text.transform)) + "\tTrue");
                        JournalLookup("log", "history:" + index, source, text.text ?? "");
                    }
                    if (logEntries.Count != history.Length)
                        JournalLine("UNAVAILABLE\tlog.entry_count\t真实历史数量与控件数量不一致，不能完整绑定来源");
                }
                yield return JournalRoundTrip("log", log, history, logEntries);
                AmbientLogFormatterProbe.Run(RequiredField(log, "ht"), outputDirectory);
                if (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_LOG_SCROLL") == "1")
                    yield return LogScrollAnchorProbe.Capture(log, outputDirectory);
                if (!String.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_LOG_SPEAKERS")))
                    yield return LogSpeakerLayoutProbe.Capture(log, outputDirectory);
            }
        }
    }

    private void FailSettingsOptions(Exception error)
    {
        if (settingsOptionsFinished) return;
        settingsOptionsFinished = true;
        if (settingsOptionsReport == null) settingsOptionsReport = new StringBuilder();
        SettingsOptionsLine("FAILURE\t" + ReportText(error.GetType().Name + ": " + error.Message));
        SettingsOptionsLine("STATUS\tFAILED");
        Logger.LogError("逐档设置验证失败：" + error);
    }

    // 将迭代器推进放在异常边界内；失败和未完成都留下记录，不能冒充验证通过。
    private IEnumerator GuardSettingsOptions()
    {
        settingsOptionsReport = new StringBuilder();
        SettingsOptionsLine("STATUS\tSTARTED");
        SettingsOptionsLine("FORMAT\tOPTION slot index source_base64 text_base64 mode overflow active");
        SettingsOptionsLine("SAVE_WRITE_GUARD_ACTIVE\t" + saveGuardActive);
        var routine = ProbeSettingsOptions();
        while (true)
        {
            bool more;
            object current = null;
            try
            {
                more = routine.MoveNext();
                if (more) current = routine.Current;
            }
            catch (Exception error)
            {
                FailSettingsOptions(error);
                yield break;
            }
            if (!more) yield break;
            yield return current;
        }
    }

    private int SliderIndex(object slider)
    {
        return ((Func<int>)RequiredField(slider, "GetValue"))();
    }

    private void ClickSettingsButton(object button)
    {
        var component = button as Component;
        if (component == null || !component.gameObject.activeInHierarchy)
            throw new InvalidOperationException("设置按钮不属于当前激活页面");
        var selectable = button as Selectable;
        if (selectable == null || !selectable.interactable)
            throw new InvalidOperationException("设置按钮不可交互");
        var property = button.GetType().GetProperty("OnClick", InstanceFields);
        if (property == null) throw new MissingMemberException("设置按钮缺少真实OnClick事件");
        var click = property.GetValue(button, null) as Button.ButtonClickedEvent;
        if (click == null) throw new InvalidOperationException("设置按钮OnClick类型不兼容");
        click.Invoke();
    }

    private void SettingsTab(object preferences, string name)
    {
        var toggle = RequiredField(preferences, name);
        var property = toggle.GetType().GetProperty("IsOn", InstanceFields);
        if (property == null) throw new MissingMemberException("真实设置页签缺少IsOn");
        property.SetValue(toggle, true, null);
        if (!(bool)property.GetValue(toggle, null)) throw new InvalidOperationException("真实设置页签切换失败");
        SettingsOptionsLine("TAB\t" + name);
    }

    private bool SettingsTranslatedMode()
    {
        foreach (var component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
        {
            if (component == null || component.GetType().Name != "TranslationToggle") continue;
            var state = component.GetType().GetMethod("IsTranslatedMode", BindingFlags.Public | BindingFlags.Instance);
            var mode = state == null ? null : state.Invoke(component, null);
            if (mode is bool) return (bool)mode;
        }
        throw new InvalidOperationException("F8插件或翻译模式尚未就绪");
    }

    private void SetSettingsTranslatedMode(bool translated)
    {
        if (SettingsTranslatedMode() == translated) return;
        InvokeToggle(false);
        InvokeToggle(true);
        if (SettingsTranslatedMode() != translated)
            throw new InvalidOperationException("F8真实输入处理路径未切换到预期模式");
    }

    private void RecordSettingOption(string slot, object slider, string source, string mode)
    {
        var text = RequiredField(slider, "Text") as TMP_Text;
        if (text == null || !text.gameObject.activeInHierarchy)
            throw new InvalidOperationException("设置文字不属于当前激活页面：" + slot);
        SettingsOptionsLine("OPTION\t" + slot + "\t" + SliderIndex(slider) + "\t" + ReportText(source)
            + "\t" + ReportText(text.text) + "\t" + mode + "\t" + text.isTextOverflowing
            + "\t" + text.gameObject.activeInHierarchy);
    }

    private IEnumerator ProbeSettingsOptions()
    {
        var gui = ObjectTracker.Instance.Gui;
        var preferences = RequiredField(gui, "preferencesCanvas") as Component;
        if (preferences == null || !preferences.gameObject.scene.IsValid()
            || !preferences.gameObject.scene.isLoaded || !preferences.gameObject.activeInHierarchy)
            throw new InvalidOperationException("当前真实PreferencesUI未打开");
        var actualState = RequiredProperty(ObjectTracker.Instance.Info, "State");
        var originalPreferences = RequiredProperty(actualState, "Preferences");
        var originalSystemConfig = RequiredProperty(actualState, "SystemConfig");
        var localPreferences = RequiredProperty(preferences, "preferences");
        var localSystemConfig = RequiredProperty(preferences, "systemConfig");
        bool preferencesCloned = !ReferenceEquals(localPreferences, originalPreferences);
        bool systemConfigCloned = !ReferenceEquals(localSystemConfig, originalSystemConfig);
        SettingsOptionsLine("SCOPE\tpreferences_clone\t" + preferencesCloned);
        SettingsOptionsLine("SCOPE\tsystem_config_clone\t" + systemConfigCloned);
        if (!saveGuardActive || !preferencesCloned || !systemConfigCloned)
            throw new InvalidOperationException("真实设置页未处于隔离克隆配置范围");

        var gameUi = RequiredField(preferences, "gameUi");
        var graphicsUi = RequiredField(preferences, "graphicsUi");
        string[] slots = { "TextSpeed", "AlternateCostumes", "Quality", "ScreenMode" };
        object[] sliders = { RequiredField(gameUi, slots[0]), RequiredField(gameUi, slots[1]),
            RequiredField(graphicsUi, slots[2]), RequiredField(graphicsUi, slots[3]) };
        var resolution = RequiredField(graphicsUi, "Resolution");
        for (int index = 0; index < slots.Length; index++)
        {
            var names = (string[])RequiredField(sliders[index], "names");
            SettingsOptionsLine("INITIAL\t" + slots[index] + "\t" + SliderIndex(sliders[index])
                + "\t" + names.Length + "\t" + (index < 2 ? "preferences_clone" : "system_config_clone"));
        }
        SettingsOptionsLine("INITIAL\tResolution\t" + SliderIndex(resolution) + "\t"
            + ((string[])RequiredField(resolution, "names")).Length + "\tsystem_config_clone");
        SetSettingsTranslatedMode(true);
        yield return new WaitForSecondsRealtime(0.4f);
        int translatedCount = 0;
        for (int index = 0; index < slots.Length; index++)
        {
            SettingsTab(preferences, index < 2 ? "gameplayToggle" : "graphicsToggle");
            yield return new WaitForSecondsRealtime(0.4f);
            var slider = sliders[index];
            var names = (string[])RequiredField(slider, "names");
            if (names.Length == 0) throw new InvalidOperationException("真实选项列表为空：" + slots[index]);
            while (SliderIndex(slider) > 0)
            {
                int before = SliderIndex(slider);
                ClickSettingsButton(RequiredField(slider, "DownButton"));
                yield return new WaitForSecondsRealtime(0.4f);
                if (SliderIndex(slider) != before - 1)
                    throw new InvalidOperationException("真实减档按钮未修改索引：" + slots[index]);
            }
            for (int option = 0; option < names.Length; option++)
            {
                if (SliderIndex(slider) != option)
                    throw new InvalidOperationException("真实选项索引与遍历档位不一致：" + slots[index]);
                RecordSettingOption(slots[index], slider, names[option], "translated");
                translatedCount++;
                if (option + 1 < names.Length)
                {
                    ClickSettingsButton(RequiredField(slider, "UpButton"));
                    yield return new WaitForSecondsRealtime(0.4f);
                }
            }
            SetSettingsTranslatedMode(false);
            yield return new WaitForSecondsRealtime(0.4f);
            RecordSettingOption(slots[index], slider, names[names.Length - 1], "original");
            SetSettingsTranslatedMode(true);
            yield return new WaitForSecondsRealtime(0.4f);
            RecordSettingOption(slots[index], slider, names[names.Length - 1], "restored");
        }
        // 屏幕模式仍只写设置页的克隆配置；不点击确认，不应用实际显示或音量设置。
        var screenMode = sliders[3];
        var screenNames = (string[])RequiredField(screenMode, "names");
        int borderless = Array.IndexOf(screenNames, "Borderless");
        if (borderless < 0) throw new InvalidOperationException("真实屏幕模式缺少Borderless");
        while (SliderIndex(screenMode) != borderless)
        {
            int before = SliderIndex(screenMode);
            ClickSettingsButton(RequiredField(screenMode, before > borderless ? "DownButton" : "UpButton"));
            yield return new WaitForSecondsRealtime(0.4f);
            if (SliderIndex(screenMode) == before) throw new InvalidOperationException("无法通过真实按钮选中Borderless");
        }
        var refresh = resolution.GetType().GetMethod("Refresh", InstanceFields);
        if (refresh == null) throw new MissingMemberException("分辨率滑块缺少Refresh");
        refresh.Invoke(resolution, null);
        yield return new WaitForSecondsRealtime(0.4f);
        var disabledText = ((Func<string>)RequiredField(resolution, "GetDisabledText"))();
        if (disabledText != "Native") throw new InvalidOperationException("无边框分辨率未进入真实Native分支");
        RecordSettingOption("Resolution", resolution, disabledText, "translated");
        translatedCount++;
        SetSettingsTranslatedMode(false);
        yield return new WaitForSecondsRealtime(0.4f);
        RecordSettingOption("Resolution", resolution, disabledText, "original");
        SetSettingsTranslatedMode(true);
        yield return new WaitForSecondsRealtime(0.4f);
        RecordSettingOption("Resolution", resolution, disabledText, "restored");
        ClickSettingsButton(RequiredField(preferences, "cancelButton"));
        yield return new WaitForSecondsRealtime(0.4f);
        bool cancelled = !preferences.gameObject.activeInHierarchy;
        SettingsOptionsLine("CANCELLED\t" + cancelled);
        var finalState = RequiredProperty(ObjectTracker.Instance.Info, "State");
        bool scopesRetained = ReferenceEquals(originalPreferences, RequiredProperty(finalState, "Preferences"))
            && ReferenceEquals(originalSystemConfig, RequiredProperty(finalState, "SystemConfig"));
        SettingsOptionsLine("SCOPES_RETAINED\t" + scopesRetained);
        if (!cancelled || !scopesRetained)
            throw new InvalidOperationException("设置页未正常取消关闭");
        SettingsOptionsLine("TRANSLATED_OPTION_COUNT\t" + translatedCount);
        SettingsOptionsLine("STATUS\tCOMPLETE");
        settingsOptionsFinished = true;
        Logger.LogInfo("真实设置组件逐档采集结束，已取消关闭；中文语义与溢出由外部断言核对。");
    }

    // 只由临时后台探针安装，不分发到用户补丁；离开进程后恢复游戏正常保存。
    public static bool BlockSaveWrite()
    {
        blockedSaveWrites++;
        return false;
    }

    // 仅临时无窗口探针安装；禁止后台配置应用重新创建实际渲染窗口。
    public static bool BlockProbeResolutionChange()
    {
        if (!Application.isBatchMode) return true;
        Debug.Log("ElsinoreHan后台诊断跳过显示质量与分辨率应用，保持NullGfx无窗口模式。");
        return false;
    }

    // 分享诊断仅选择并预览信息；即使控件回调异常，也不进入提交和剧情变更入口。
    public static bool BlockProbePresentationSubmit()
    {
        if (!Application.isBatchMode) return true;
        blockedPresentationSubmits++;
        return false;
    }

    public static bool UseIsolatedSaveDirectory(ref string __result)
    {
        __result = isolatedSaveDirectory;
        return false;
    }

    public static bool BlockSaveMigration(ref bool __result)
    {
        __result = false;
        return false;
    }

    private void InvokeToggle(bool keyDown)
    {
        foreach (var component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
        {
            if (component == null || component.GetType().Name != "TranslationToggle") continue;
            var type = component.GetType();
            var state = type.GetMethod("IsTranslatedMode", BindingFlags.Public | BindingFlags.Instance);
            var before = state.Invoke(component, null);
            var result = type.GetMethod("HandleKey", BindingFlags.Public | BindingFlags.Instance).Invoke(component, new object[] { keyDown });
            var after = state.Invoke(component, null);
            Logger.LogInfo("F8探针输入=" + keyDown + " 返回=" + result + " 前=" + before + " 后=" + after);
            if (!keyDown) Logger.LogInfo("F8_RELEASE_NO_CHANGE=" + Equals(before, after));
            return;
        }
        Logger.LogError("F8探针未找到运行中的热键插件。");
    }

    private void Capture(string name)
    {
            var directory = outputDirectory;
            Directory.CreateDirectory(directory);
            var report = new StringBuilder();
            report.AppendLine("SAVE_WRITE_GUARD_ACTIVE=" + saveGuardActive + " BLOCKED=" + blockedSaveWrites);
            report.AppendLine("PHYSICAL_INPUT_GUARD_ACTIVE=" + physicalInputGuardActive + " BLOCKED=" + blockedPhysicalButtons);
            report.AppendLine("PHYSICAL_INPUT_MODULES_DISABLED=" + disabledPhysicalInputModules);
            var cacheCasesPath = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_CACHE_CASES");
            if (name == "menu") StrictLogCacheProbe.Run(directory);
            if (name == "menu" && !string.IsNullOrEmpty(cacheCasesPath))
            {
                try
                {
                    Type api = null;
                    foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
                    {
                        api = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.AutoTranslator", false);
                        if (api != null) break;
                    }
                    var instance = api.GetProperty("Default").GetValue(null, null);
                    var contract = api.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.ITranslator");
                    var lookup = contract.GetMethod("TryTranslate", new Type[] { typeof(string), typeof(string).MakeByRefType() });
                    int count = 0;
                    bool passed = true;
                    foreach (var line in File.ReadAllLines(cacheCasesPath, Encoding.UTF8))
                    {
                        if (string.IsNullOrEmpty(line)) continue;
                        var fields = line.Split('\t');
                        var source = Encoding.UTF8.GetString(Convert.FromBase64String(fields[1]));
                        var expected = Encoding.UTF8.GetString(Convert.FromBase64String(fields[2]));
                        var arguments = new object[] { source, null };
                        var found = (bool)lookup.Invoke(instance, arguments);
                        bool matches = found && (string)arguments[1] == expected;
                        passed &= matches;
                        count++;
                        report.AppendLine("CACHE_CASE=" + fields[0] + " LENGTH=" + source.Length + " MATCH=" + matches);
                        if (!matches) report.AppendLine("CACHE_ACTUAL=" + fields[0] + " FOUND=" + found + " TEXT_BASE64=" + Convert.ToBase64String(Encoding.UTF8.GetBytes((string)arguments[1] ?? "")));
                    }
                    report.AppendLine("FROZEN_CACHE_CASES=" + passed + " COUNT=" + count);
                }
                catch (Exception error)
                {
                    report.AppendLine("FROZEN_CACHE_CASES=False ERROR=" + error.GetType().Name);
                }
            }
            foreach (var font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (font.name == (Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_FONT_NAME") ?? "ARIALUNI SDF"))
                {
                    report.AppendLine("LOADED_FONT=" + font.name + " VERSION=" + font.version
                        + " GLYPHS_继续游戏设置退出=" + font.HasCharacters("继续游戏设置退出"));
                    if (name == "menu") FontRegressionProbe.Capture(font, directory);
                    var charactersPath = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_CHARACTERS");
                    if (!string.IsNullOrEmpty(charactersPath) && File.Exists(charactersPath))
                    {
                        var characters = File.ReadAllText(charactersPath, Encoding.UTF8);
                        report.AppendLine("FULL_CHINESE_GLYPHS=" + font.HasCharacters(characters) + " COUNT=" + characters.Length);
                    }
                }
            }
            foreach (var dropdown in Resources.FindObjectsOfTypeAll<Dropdown>())
            {
                if (!dropdown.gameObject.scene.IsValid() || !dropdown.gameObject.scene.isLoaded) continue;
                foreach (var option in dropdown.options)
                    if (option != null && !string.IsNullOrEmpty(option.text))
                        report.AppendLine("DROPDOWN_OPTION=" + dropdown.name + "|" + option.text.Replace("\n", "\\n"));
            }
            foreach (var text in Resources.FindObjectsOfTypeAll<TMP_Text>())
            {
                if (!text.gameObject.scene.IsValid() || !text.gameObject.scene.isLoaded) continue;
                report.AppendLine("OBJECT=" + text.name + " ACTIVE=" + text.gameObject.activeInHierarchy);
                report.AppendLine("TEXT=" + text.text.Replace("\n", "\\n"));
                report.AppendLine("FONT=" + (text.font == null ? "null" : text.font.name));
                if (text.gameObject.activeInHierarchy)
                    report.AppendLine("OVERFLOW=" + text.isTextOverflowing + " RECT=" + text.rectTransform.rect);
                if (text.font != null && text.font.fallbackFontAssetTable != null)
                {
                    foreach (var fallback in text.font.fallbackFontAssetTable)
                    {
                        if (fallback == null) continue;
                        report.AppendLine("FALLBACK=" + fallback.name + " VERSION=" + fallback.version);
                        report.AppendLine("GLYPHS_开始新游戏=" + fallback.HasCharacters("开始新游戏"));
                    }
                }
            }
            File.WriteAllText(Path.Combine(directory, name + "-texts.txt"), report.ToString(), new UTF8Encoding(false));
            // -nographics 后台模式只采集日志，既有渲染截图单独保留。
            if (!Application.isBatchMode)
                ScreenCapture.CaptureScreenshot(Path.Combine(directory, name + ".png"));
            Logger.LogInfo("真实已加载场景文字与字体已记录：" + directory);
    }
}
