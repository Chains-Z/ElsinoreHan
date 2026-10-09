using System;
using System.Reflection;
using System.Text;
using BepInEx;
using HarmonyLib;
using TMPro;
using UnityEngine;
using XUnity.AutoTranslator.Plugin.Core;

// 复用 XUnity 已保留的原文和译文，不反向翻译，不修改存档或游戏资源。
[BepInPlugin("elsinorehan.translationtoggle", "ElsinoreHan Translation Toggle", "1.3.0")]
[BepInDependency("gravydevsupreme.xunity.autotranslator")]
public sealed class TranslationToggle : BaseUnityPlugin
{
    private Type translatorType;
    private FieldInfo currentField;
    private FieldInfo modeField;
    private MethodInfo toggleMethod;
    private bool unavailableLogged;
    private static long builderPrefixCalls;
    private static long stringPrefixCalls;
    private static FieldInfo textCacheField;
    private static MethodInfo addTranslationToCache;
    private static object fullTranslationType;
    private static BepInEx.Logging.ManualLogSource compatibilityLogger;
    private static bool cacheFailureLogged;
    public const byte ChineseItalicStyle = 10;
    public static byte? OriginalChineseItalicStyle;

    private void Awake()
    {
        compatibilityLogger = Logger;
        var translator = AutoTranslator.Default;
        textCacheField = translator.GetType().GetField("TextCache", BindingFlags.Instance | BindingFlags.NonPublic);
        var cache = textCacheField.GetValue(translator);
        addTranslationToCache = cache.GetType().GetMethod("AddTranslationToCache", BindingFlags.Instance | BindingFlags.NonPublic);
        fullTranslationType = Enum.Parse(addTranslationToCache.GetParameters()[3].ParameterType, "Full");
        // 本游戏的 TMP 1.4.0 只将 StringBuilder 写入解析缓冲区，text getter 仍是旧值。
        // 改走正常文本入口，让 XUnity 保存完整原文并翻译；不提前改写成中文。
        var compatibility = new Harmony("elsinorehan.translationtoggle.tmpcompatibility");
        compatibility.Patch(typeof(TMP_Text).GetMethod("SetText", new Type[] { typeof(StringBuilder) }),
            prefix: new HarmonyMethod(typeof(TranslationToggle).GetMethod("SetBuilderThroughText", BindingFlags.Public | BindingFlags.Static)));
        compatibility.Patch(typeof(TMP_Text).GetMethod("SetText", new Type[] { typeof(string), typeof(bool) }),
            prefix: new HarmonyMethod(typeof(TranslationToggle).GetMethod("SetStringThroughText", BindingFlags.Public | BindingFlags.Static)));
        compatibility.Patch(typeof(TMP_Text).GetProperty("text").GetSetMethod(),
            prefix: new HarmonyMethod(typeof(TranslationToggle).GetMethod("PrepareOfflineText", BindingFlags.Public | BindingFlags.Static)));
        compatibility.Patch(typeof(TMP_FontAsset).GetMethod("ReadFontAssetDefinition", Type.EmptyTypes),
            postfix: new HarmonyMethod(typeof(TranslationToggle).GetMethod("ConfigureChineseItalic", BindingFlags.Public | BindingFlags.Static)));
        foreach (TMP_FontAsset font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>()) ConfigureChineseItalic(font);
        Logger.LogInfo("TMP StringBuilder 与字符串 SetText 文本入口兼容已启用。");
        foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            translatorType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.AutoTranslationPlugin", false);
            if (translatorType != null) break;
        }
        if (translatorType != null)
        {
            currentField = translatorType.GetField("Current", BindingFlags.Static | BindingFlags.NonPublic);
            modeField = translatorType.GetField("_isInTranslatedMode", BindingFlags.Instance | BindingFlags.NonPublic);
            toggleMethod = translatorType.GetMethod("ToggleTranslation", BindingFlags.Instance | BindingFlags.NonPublic);
        }
        if (currentField == null || modeField == null || toggleMethod == null)
        {
            enabled = false;
            Logger.LogError("XUnity 切换接口不兼容，F8扩展未启用。");
            return;
        }
        Logger.LogInfo("F8切换原文/译文已启用；使用离线原文缓存，无网络请求。");
    }

    public static bool SetBuilderThroughText(TMP_Text __instance, StringBuilder __0)
    {
        builderPrefixCalls++;
        SetOfflineText(__instance, __0 == null ? string.Empty : __0.ToString());
        return false;
    }

    public static void ConfigureChineseItalic(TMP_FontAsset __instance)
    {
        // 仅调整本补丁中文回退字体；TMP 合成斜体不增加推进宽度，过大剪切会撞字。
        if (__instance != null && String.Equals(__instance.name, "ARIALUNI SDF", StringComparison.Ordinal))
        {
            if (!OriginalChineseItalicStyle.HasValue) OriginalChineseItalicStyle = __instance.italicStyle;
            __instance.italicStyle = ChineseItalicStyle;
        }
    }

    public static bool SetStringThroughText(TMP_Text __instance, string __0)
    {
        stringPrefixCalls++;
        SetOfflineText(__instance, __0 ?? string.Empty);
        return false;
    }

    private static void SetOfflineText(TMP_Text component, string source)
    {
        // 组件仍接收原文；正常 setter 的前缀负责限定离线缓存登记。
        component.text = source;
    }

    public static void PrepareOfflineText(TMP_Text __instance, string __0)
    {
        if (!(__instance is TextMeshProUGUI) || string.IsNullOrEmpty(__0)) return;
        if (__instance.gameObject.name == "Title")
        {
            for (Transform parent = __instance.transform.parent; parent != null; parent = parent.parent)
            {
                if (parent.name != "CharactersTab") continue;
                // 人物全名只能使用标题原有的一行空间，避免换行压住独立称号。
                float maximum = __instance.enableAutoSizing ? __instance.fontSizeMax : __instance.fontSize;
                __instance.fontSizeMax = maximum;
                __instance.fontSizeMin = Math.Max(16f, maximum * 0.4f);
                __instance.enableWordWrapping = false;
                __instance.enableAutoSizing = true;
                break;
            }
        }
        bool hasEnglish = false;
        foreach (char character in __0)
        {
            if ((character >= 'A' && character <= 'Z') || (character >= 'a' && character <= 'z'))
            { hasEnglish = true; break; }
        }
        if (!hasEnglish) return;
        try
        {
            var translator = AutoTranslator.Default;
            string translated;
            if (translator != null && translator.TryTranslate(__0, out translated) && translated != __0)
            {
                // TryTranslate 不登记拆分后的完整串；即时/稳定检测路径却只查整串缓存。
                // Full、scope=-1 与当前 XUnity 一致，persist=false 不写磁盘或游戏历史。
                addTranslationToCache.Invoke(textCacheField.GetValue(translator),
                    new object[] { __0, translated, false, fullTranslationType, -1 });
            }
        }
        catch (Exception error)
        {
            // 缓存失败不能阻断游戏自己的原文赋值；仅记录一次，不泄露正文。
            if (!cacheFailureLogged)
            {
                cacheFailureLogged = true;
                compatibilityLogger.LogWarning("离线组合缓存登记失败，继续显示原文：" + error.GetType().Name);
            }
        }
    }

    private void Update()
    {
        HandleKey(Input.GetKeyDown(KeyCode.F8));
    }

    // 自动探针调用同一输入处理路径；它验证运行集成，不冒充物理键盘输入。
    public bool HandleKey(bool keyDown)
    {
        if (!keyDown || currentField == null || toggleMethod == null) return false;
        object instance = currentField.GetValue(null);
        if (instance == null)
        {
            if (!unavailableLogged)
            {
                unavailableLogged = true;
                Logger.LogWarning("译文插件尚未就绪，此次F8未执行。");
            }
            return false;
        }
        try
        {
            toggleMethod.Invoke(instance, null);
            Logger.LogInfo("F8显示模式=" + ((bool)modeField.GetValue(instance) ? "译文" : "原文"));
            return true;
        }
        catch (Exception error)
        {
            Logger.LogError("F8切换失败：" + error.GetType().Name);
            return false;
        }
    }

    public bool? IsTranslatedMode()
    {
        if (currentField == null || modeField == null) return null;
        object instance = currentField.GetValue(null);
        return instance == null ? (bool?)null : (bool)modeField.GetValue(instance);
    }
}
