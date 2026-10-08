using System;
using System.IO;
using System.Text;
using BepInEx;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

// 只记录真实场景文字与字形覆盖，避免修改游戏状态或进入存档流程。
[BepInPlugin("elsinorehan.runtimeprobe", "ElsinoreHan Runtime Probe", "0.1.0")]
public sealed class RuntimeProbe : BaseUnityPlugin
{
    private float started;
    private bool captured;
    private bool openedSettings;
    private bool capturedSettings;
    private bool audioSuspended;
    private string outputDirectory;

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
        // 自动探针只允许后台运行；普通游玩不安装此插件。
        if (!Application.isBatchMode)
        {
            Logger.LogError("探针要求 -batchmode；立即退出，禁止常规前台运行。");
            Application.Quit();
            return;
        }
        AudioListener.pause = true;
        AudioListener.volume = 0f;
        Application.targetFrameRate = 10;
        Logger.LogInfo("后台模式确认：Application.isBatchMode=True；Unity 音频已暂停。");
        Logger.LogInfo("运行时探针启动；不调用翻译服务、不进入存档。");
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
        if (!captured && Time.realtimeSinceStartup - started > 18f)
        {
            captured = true;
            Capture("menu");
        }
        if (!openedSettings && Time.realtimeSinceStartup - started > 20f)
        {
            openedSettings = true;
            foreach (var text in Resources.FindObjectsOfTypeAll<TMP_Text>())
            {
                if (!text.gameObject.scene.IsValid() || !text.gameObject.scene.isLoaded
                    || !text.gameObject.activeInHierarchy || text.text != "设置") continue;
                var pointer = new PointerEventData(EventSystem.current);
                pointer.button = PointerEventData.InputButton.Left;
                var handled = ExecuteEvents.ExecuteHierarchy(text.gameObject, pointer, ExecuteEvents.pointerClickHandler);
                if (handled == null) continue;
                Logger.LogInfo("已通过真实设置按钮的 EventSystem 指针事件打开设置界面。");
                break;
            }
        }
        if (!capturedSettings && Time.realtimeSinceStartup - started > 23f)
        {
            capturedSettings = true;
            Capture("settings");
        }
        if (Time.realtimeSinceStartup - started > 30f)
            Application.Quit();
    }

    private void Capture(string name)
    {
            var directory = outputDirectory;
            Directory.CreateDirectory(directory);
            var report = new StringBuilder();
            foreach (var font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (font.name.IndexOf("arial", StringComparison.OrdinalIgnoreCase) >= 0)
                    report.AppendLine("LOADED_FONT=" + font.name + " VERSION=" + font.version
                        + " GLYPHS_继续游戏设置退出=" + font.HasCharacters("继续游戏设置退出"));
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
