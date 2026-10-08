using System;
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
    private bool requestedPause;
    private bool requestedSplash;
    private bool saveGuardActive;
    private static int blockedSaveWrites;
    private static string isolatedSaveDirectory;

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
            saveGuardActive = true;
            Logger.LogInfo("临时诊断存档写入保护已启用：存档目录已隔离，SaveLoad.SaveData全部阻断。");
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
        if (AkSoundEngine.IsInitialized())
        {
            var result = AkSoundEngine.Suspend(true);
            if (!audioSuspended)
            {
                audioSuspended = true;
                Logger.LogInfo("Wwise 后台音频暂停结果=" + result);
            }
        }
        if (requireToggle && Time.realtimeSinceStartup - started > 12f && Time.realtimeSinceStartup - started < 18f
            && Time.realtimeSinceStartup > nextMenuCheck)
        {
            nextMenuCheck = Time.realtimeSinceStartup + 1f;
            // 从当前游戏跟踪器获取真实GUI；资源枚举也包含未使用的预制件和旧transitioner。
            var gui = ObjectTracker.Instance.Gui;
            var activeProperty = gui == null ? null : gui.GetType().GetProperty("IsMainMenuActive", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (gui != null && gui.IsInitialized && activeProperty != null && !(bool)activeProperty.GetValue(gui, null))
            {
                var transitions = gui.GetType().GetNestedType("UiTransitions", BindingFlags.Public | BindingFlags.NonPublic);
                var current = Activator.CreateInstance(transitions, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, new object[] { gui, null }, null);
                if (!requestedPause)
                {
                    requestedPause = true;
                    // 与真实Esc和暂停按钮共用合法暂停动作，让游戏自行切换时间模式。
                    transitions.GetMethod("ActivatePause").Invoke(current, null);
                    Logger.LogInfo("后台探针已通过真实暂停动作请求Pause，等待覆盖层就绪。");
                }
                else if (!requestedSplash)
                {
                    var overlay = gui.GetType().GetProperty("CurrentlyActiveOverlayCanvas", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance).GetValue(gui, null);
                    var pause = gui.GetType().GetField("pauseCanvas", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance).GetValue(gui);
                    if (overlay != null && Equals(overlay, pause))
                    {
                        requestedSplash = true;
                        transitions.GetMethod("ActivateSplashScreen").Invoke(current, null);
                        Logger.LogInfo("真实暂停覆盖层就绪，已一次性展示SplashScreen；不点击新游戏或继续。");
                    }
                }
            }
        }
        if (!captured && Time.realtimeSinceStartup - started > 18f)
        {
            captured = true;
            Capture("menu");
        }
        if (!openedSettings && Time.realtimeSinceStartup - started > 20f)
        {
            openedSettings = true;
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
                Logger.LogInfo("已通过真实设置按钮的 EventSystem 指针事件打开设置界面。");
                break;
            }
        }
        if (requireToggle && captured && !showedOriginal && Time.realtimeSinceStartup - started > 19f)
        {
            showedOriginal = true;
            InvokeToggle(false);
            InvokeToggle(true);
            Capture("original-menu");
        }
        if (requireToggle && showedOriginal && !restoredTranslated && Time.realtimeSinceStartup - started > 19.5f)
        {
            restoredTranslated = true;
            InvokeToggle(true);
            Capture("restored-menu");
        }
        if (!capturedSettings && Time.realtimeSinceStartup - started > 23f)
        {
            capturedSettings = true;
            Capture("settings");
        }
        if (Time.realtimeSinceStartup - started > 30f)
            Application.Quit();
    }

    // 只由临时后台探针安装，不分发到用户补丁；离开进程后恢复游戏正常保存。
    public static bool BlockSaveWrite()
    {
        blockedSaveWrites++;
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
            var cacheCasesPath = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_CACHE_CASES");
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
                if (font.name.IndexOf("arial", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    report.AppendLine("LOADED_FONT=" + font.name + " VERSION=" + font.version
                        + " GLYPHS_继续游戏设置退出=" + font.HasCharacters("继续游戏设置退出"));
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
