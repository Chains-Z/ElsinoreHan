# 汉化补丁技术样板验证

日期：2026-10-09。本轮已从静态分析推进到真实游戏运行。未调用 GLM 或其他翻译 API；样板词表为少量手工技术测试译文，不代表最终文风。

## 已取得的结果

- BepInEx 5.4.23.5 x86 与 XUnity.AutoTranslator 5.6.2 Mono 在本机游戏成功加载；真实 TMP 版本为 1.4.0。
- 中文 fallback 字体加载成功，`继续游戏设置退出` 的字形查询全部通过。
- 真实主菜单显示“继续游戏 / 设置 / 退出游戏”。自动游戏截图已检查，未观察到缺字方框、裁切或明显错位；三个菜单组件的 `isTextOverflowing` 均为 `False`。
- 自动设置导航已跑通：通过真实 `Elsinore.Ui.ElsinoreButton` 的 `IPointerClickHandler` 投递 Unity EventSystem 指针事件，未改任何设置。设置页的 Graphics、Audio、Gameplay 文本组件出现，激活文本组件没有被 TMP 标记溢出。
- 对菜单漏译、未打开设置仍误判通过、隐藏文本误计、实际溢出四种失败分支补了低层回归，4 项测试通过。真实后台 UI 集成断言 7 项通过。
- 原始 `Elsinore.exe`、`UnityPlayer.dll`、`resources.assets`、`Assembly-CSharp.dll` 的安装前后 SHA256 完全相同。

这是主菜单渲染验收与真实游戏 UI 集成探针。没有点击“继续游戏”，没有进入剧情或存档流程，尚未验证对白、资料、长文换行、剧情分支覆盖和全量翻译。后台模式只检查加载与组件状态，不能证明设置页最终像素排版通过；`activeInHierarchy` 也不等同于像素可见，报告中的 `visible_*` 字段应按激活组件理解。

## 证据入口

| 文件 | 含义 |
| --- | --- |
| `runtime/evidence/menu-fixed.png` | 第二轮真实主菜单自动截图，三按钮均中文 |
| `runtime/evidence/menu-render-verification.json` | 主菜单截图检查结论，独立于后台结果 |
| `runtime/evidence/headless-ui-verification.json` | 最终真实后台 UI 集成断言，7 项通过 |
| `runtime/evidence/headless-process.json` | 独立运行编号、退出码、后台/静音确认和进程配置 |
| `runtime/evidence/headless/17ee44453c994de0b925fbe5e68c5ef4/` | 最终本轮的独立原始组件记录、进程记录与断言 |
| `runtime/evidence/original-game-integrity.json` | 四项原始游戏文件哈希前后比较 |
| `runtime/evidence/dependencies.json` | 固定依赖版本、下载来源和 SHA256 |
| `runtime/evidence/installed-files.json` | 初次安装新增文件清单；其中诊断 DLL 已移除 |

## 自动化和不打扰工作

最初前台运行由游戏内 `ScreenCapture.CaptureScreenshot` 自动截图，无需用户手工截图。后续用户明确要求测试不得抢前台或发声，因此不再执行常规前台启动。

现在的 `run-headless-probe.ps1` 固定使用 `-batchmode -nographics -nosound`，后台隐藏启动，进程 `BelowNormal` 优先级，探针 `Application.targetFrameRate=10`。探针确认 `Application.isBatchMode=True`，暂停 Unity AudioListener，并在 Wwise 初始化后维持 `AkSoundEngine.Suspend(true)`；本轮返回 `AK_Success`。不能只依赖 `-nosound`，因为游戏使用 Wwise。

本轮监测主窗口句柄始终为 0，退出码为 0。该监测针对主窗口，不足以保证任意未来版本都不会出现其他辅助窗口。禁止把常规 `Start-Process -WindowStyle Hidden` 当成“不抢焦点”的保证：游戏此前会由 Steam 重新启动，原参数可能丢失。后台脚本临时创建本游戏 `steam_appid.txt` 保持当前批处理启动参数，结束后删除，仅在文件此前不存在时创建。

探针只允许带有效独立运行编号的后台运行；缺少编号或未进入 batchmode 时退出。每轮使用 GUID 独立证据目录，并检查新产物的时间与进程退出码，防止复制上一轮文件冒充成功。诊断 DLL 和临时 appid 的清理位于 `finally`。最终已确认没有运行中的 Elsinore 进程，没有诊断 DLL，没有临时 appid 文件。

后台 `-nographics` 不采集渲染截图，已有主菜单截图来自此前真实有图形运行；后续渲染测试若确有必要，应另行实现并验证不激活的小窗口/离屏渲染方式，继续遵守用户不打扰工作的约束。

## 当前安装状态与操作

游戏目录仍留有本次添加的 BepInEx、XUnity、字体和离线样板词表。没有覆盖原游戏资源和程序集。网络翻译 Endpoint、FallbackEndpoint 均为空，安装时排除所有 `Translators` 端点程序集；正常游玩不会调用翻译 API。诊断插件已移除，正常启动不会自动导航、静音或退出。

只禁用整个样板，不删除文件：

```powershell
./tools/patch/set-sample-enabled.ps1 -Enabled $false
```

重新启用：

```powershell
./tools/patch/set-sample-enabled.ps1 -Enabled $true
```

从干净游戏目录复现安装（联网和游戏目录写入按 AGENTS 提权）：

```powershell
./tools/patch/download-dependencies.ps1
./tools/patch/install-sample.ps1
```

只运行不打扰前台的后台集成探针：

```powershell
./tools/patch/run-headless-probe.ps1
python -m unittest discover -s tools/patch -p test_verify_probe.py
```

安装脚本检测到既有 BepInEx、注入文件或字体时拒绝覆盖。下载包和字体仅在本地 `runtime/downloads`、`runtime/vendor` 缓存，未纳入 Git。编译使用本机已有 .NET Framework `csc.exe` 与游戏实际 Managed DLL，无需恢复 NuGet 依赖。

## 字体与后续限制

当前技术样板使用 XUnity 官方字体包中的 `arialuni_sdf_u2018`。日志提示字体资产版本 1.1.0 与游戏 TMP 1.4.0 不同，但主菜单实际显示成功。这个结论只支持当前样板，仍需检查长文、字形范围与排版。

Arial Unicode 字体授权不清晰，该字体不纳入补丁分发。后续正式补丁应选用授权明确的中文字体，在兼容的 Unity/TMP 环境生成资产；可考察开源字体及对应构建工具。XUnity 5.6.2 的“直接指定系统字体”要求 TMP 3.2.0+，不适合直接套到本游戏 TMP 1.4.0。

第一轮仅翻到“设置”，原因是真实菜单写的是 `Continue Game`、`Quit Game`，不是猜测的缩写。已据运行记录补精确词条并补回归。第一次设置导航失败，是把游戏专用按钮当成 `UnityEngine.UI.Button`；已改用真实指针接口，并由后台集成链确认成功。

## 资料来源

- [BepInEx 5.4.23.5 官方发布](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.5)。
- [XUnity.AutoTranslator 5.6.2 官方发布](https://github.com/bbepis/XUnity.AutoTranslator/releases/tag/v5.6.2)，本地包 SHA256 与官方公布值一致。
- [XUnity 字体与离线词表说明](https://github.com/bbepis/XUnity.AutoTranslator/blob/v5.6.2/README.md)。
- [XUnity 官方 TMP 字体包所在发布](https://github.com/bbepis/XUnity.AutoTranslator/releases/tag/v5.5.0)。
- [MoeFont 多版本 TMP 字体资产](https://github.com/sorrowmoil/sorrowmoil-MoeFont-for-XUnity.AutoTranslator)，可参考构建方式，字体授权仍应分别核实。
- [Unity Standalone Player 命令行参数说明](https://docs.unity3d.com/2018.4/Documentation/Manual/CommandLineArguments.html)。
