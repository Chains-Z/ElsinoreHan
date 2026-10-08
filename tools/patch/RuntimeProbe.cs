using System;
using System.Collections;
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
    private bool requireSettingsOptions;
    private bool settingsOptionsFinished;
    private StringBuilder settingsOptionsReport;
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
        requireSettingsOptions = Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SETTINGS_OPTIONS") == "1";
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
        if ((requireToggle || requireSettingsOptions) && Time.realtimeSinceStartup - started > 12f && Time.realtimeSinceStartup - started < 18f
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
            if (requireSettingsOptions)
                StartCoroutine(GuardSettingsOptions());
        }
        if (Time.realtimeSinceStartup - started > (requireSettingsOptions ? 45f : 30f))
        {
            if (requireSettingsOptions && !settingsOptionsFinished)
                FailSettingsOptions(new TimeoutException("逐档设置验证未在45秒内结束"));
            Application.Quit();
        }
    }

    private const BindingFlags InstanceFields = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

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
