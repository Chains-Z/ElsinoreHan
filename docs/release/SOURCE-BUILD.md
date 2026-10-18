# ElsinoreHan 插件源码与构建

本归档对应内部兼容插件1.5.15，采用LGPL-2.1-or-later。完整许可证见 LICENSE，范围说明见 LICENSE-SCOPE.md。归档包含13个编译用C#源文件和原始 tools/patch/build-toggle.ps1，不包含游戏、字体、第三方DLL、译文、探针或玩家存档。

## 构建条件

- Windows，具备 .NET Framework 4 的 C# 编译器：%WINDIR%/Microsoft.NET/Framework/v4.0.30319/csc.exe。
- 自行拥有 Windows 版《Elsinore》1.4.1（3678）。引用其 Elsinore_Data/Managed 中的Unity程序集，游戏本身不由本项目再分发。
- BepInEx 5.4.23.5的 BepInEx.dll、0Harmony.dll，以及 XUnity.AutoTranslator 5.6.2的 XUnity.AutoTranslator.Plugin.Core.dll。可使用同版补丁中的文件；各自许可不变。

## 操作

把本源码归档解压到独立文件夹，以该文件夹为当前目录打开PowerShell。下面的 gamePath 应为含 Elsinore.exe 的目录；游戏应先退出。

```powershell
$gamePath = Read-Host '请输入包含 Elsinore.exe 的游戏目录'
$buildDirectories = @(
    'runtime/build',
    'runtime/vendor/BepInEx5/BepInEx/core',
    'runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator'
)
foreach ($directory in $buildDirectories) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
Copy-Item -LiteralPath (Join-Path $gamePath 'BepInEx/core/BepInEx.dll') -Destination 'runtime/vendor/BepInEx5/BepInEx/core/BepInEx.dll'
Copy-Item -LiteralPath (Join-Path $gamePath 'BepInEx/core/0Harmony.dll') -Destination 'runtime/vendor/BepInEx5/BepInEx/core/0Harmony.dll'
Copy-Item -LiteralPath (Join-Path $gamePath 'BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll') -Destination 'runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll'
./tools/patch/build-toggle.ps1 -GamePath $gamePath
```

输出为 runtime/build/ElsinoreHan.TranslationToggle.dll。这个编译器每次编译会生成新的模块标识，重新编译的DLL不要求与发行DLL逐字节相同。正式发布时，打包器另将全部编译源文件逐项与原构建记录中的输入哈希比对，并核对该记录的输出哈希与已安装DLL一致，防止随附错误版本源码。

修改后可在游戏关闭时自行替换游戏目录中的 BepInEx/plugins/ElsinoreHan.TranslationToggle.dll。建议自行保留需要恢复的原文件。公开包的安装器会拒绝覆盖内容未知的修改版DLL，不能用它强行接管该文件；你可以直接维护自己构建的版本。

归档不包含自动化验收探针，也不会启动游戏或修改存档。完整工具、历史及反馈入口：https://github.com/Chains-Z/ElsinoreHan
