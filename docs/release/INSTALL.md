# 安装、更新与卸载

适用游戏：Windows 版《Elsinore》1.4.1（3678），支持 64 位 Windows。开始前请保存进度并完全退出游戏。

## 首次安装

1.在 Steam 库中右键《Elsinore》，通过“管理”中的“浏览本地文件”找到游戏目录。此目录应直接包含 `Elsinore.exe`。

2.将 ZIP 中的所有内容直接解压到该目录，保持目录结构。解压后 `winhttp.dll`、`doorstop_config.ini` 和 `BepInEx/` 应与 `Elsinore.exe` 同级；说明及辅助工具位于 `ElsinoreHan/`。

3.正常从 Steam 启动游戏，确认文字显示为中文，并按 F8 检查英文切换。无需运行额外脚本。

直接解压适用于首次安装到没有其他模组的游戏目录。已有模组或更新旧补丁时，直接解压可能覆盖同名加载器或配置，无法预先检查冲突；建议改用下方的可选安装器。

## 可选安装器：检查冲突与更新

先将完整 ZIP 解压到游戏目录以外的普通文件夹，保留所有相对路径，再双击其中 `ElsinoreHan/Install.cmd`，粘贴游戏目录并回车。等待成功提示；出现错误时先处理原因。

安装脚本在本机运行，不下载文件，不需要管理员权限；游戏安装目录必须对当前用户可写。它核对包中文件和目标目录，记录由其安装的文件，供后续更新与卸载使用。

安装器不会备份旧补丁。它只更新经核对的本补丁文件；遇到同名冲突、被手动修改的文件、无法识别的旧版本或不兼容的加载器时会停止。旧个人版本仅在其文件与已知版本准确匹配时才能接管。处理方法见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

若使用 PowerShell，请在已解压包的 `ElsinoreHan/` 目录打开 PowerShell，运行：

```powershell
$gamePath = Read-Host '请输入包含 Elsinore.exe 的游戏目录'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -GamePath $gamePath
```

此命令只为当前脚本进程指定执行策略，不修改系统的永久执行策略。若设备由单位管理并禁止脚本运行，请遵循设备管理要求。

以后使用新版辅助安装器更新时，请保留游戏目录中的 `ElsinoreHan.install.json`，它记录文件归属，不要手动修改。直接解压安装不会自动生成该记录。

## 临时停用

退出游戏，打开游戏目录下的 `doorstop_config.ini`，将 `[General]` 下的 `enabled=true` 改为 `enabled=false`，保存后重新启动游戏即可停用加载器。改回 `true` 可恢复。

此开关也会停用通过同一个加载器运行的其他模组。修改后的配置会被卸载器保留；如需完整卸载，请先恢复修改前的内容。

## 卸载

退出游戏，双击 `ElsinoreHan/Uninstall.cmd`，输入同一个游戏目录。也可在 `ElsinoreHan/` 目录运行：

```powershell
$gamePath = Read-Host '请输入包含 Elsinore.exe 的游戏目录'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1 -GamePath $gamePath
```

通过辅助安装器安装时，卸载器依据 `ElsinoreHan.install.json` 仅删除本补丁拥有、且内容仍与记录一致的文件。安装时已经存在的相同文件视为共享文件，不会认领或删除；其他模组文件也不会删除。

若安装后加入了其他模组，或共享配置、依赖发生变化，卸载器会保留共享运行环境并逐项报告，同时保留残余归属记录，只清理未修改的本项目独有文件。

直接解压安装、没有文件归属记录时，卸载器只清除与本版准确匹配的中文字体、兼容插件、词表及本项目字体许可文件。通用加载器、翻译组件和配置会保留，因为无法判断它们此前是否被其他模组使用。此方式可以撤去中文补丁，但不会清空全部第三方文件。

若文件在安装后被修改，卸载器会保留并列出这些文件，同时保留对应安装记录。请根据提示检查；恢复其安装时内容后可再次运行卸载。不要直接删除整个 `BepInEx/` 目录，以免影响其他模组。运行后留下空目录或共享加载器文件属于可能的正常结果。

卸载完成后，文档、源码和辅助脚本所在的 `ElsinoreHan/` 文件夹可自行删除。保留它们也不会影响游戏。

补丁文件不替换游戏原始可执行文件、`UnityPlayer.dll`、`resources.assets`、`Assembly-CSharp.dll` 或玩家存档，也不自动备份存档。如需自行备份，先退出游戏，再复制 `%APPDATA%\Golden Glitch Studios\Elsinore` 到自己保管的位置。
