using System;
using System.Reflection;
using BepInEx;
using UnityEngine;

// 复用 XUnity 已保留的原文和译文，不反向翻译，不修改存档或游戏资源。
[BepInPlugin("elsinorehan.translationtoggle", "ElsinoreHan Translation Toggle", "1.0.0")]
[BepInDependency("gravydevsupreme.xunity.autotranslator")]
public sealed class TranslationToggle : BaseUnityPlugin
{
    private Type translatorType;
    private FieldInfo currentField;
    private FieldInfo modeField;
    private MethodInfo toggleMethod;
    private bool unavailableLogged;

    private void Awake()
    {
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
