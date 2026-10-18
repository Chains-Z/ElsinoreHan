# 安装方法

适用于 Windows 版《Elsinore》1.4.1（3678），支持 64 位 Windows。

## 首次安装：解压即可

1.保存进度，完全退出游戏。

2.在 Steam 游戏库中右键《Elsinore》，选择“管理”→“浏览本地文件”。打开的文件夹里应当能看到 Elsinore.exe。

3.把补丁压缩包里的全部文件解压到这个文件夹。winhttp.dll、doorstop_config.ini 和 BepInEx 文件夹应与 Elsinore.exe 放在一起，不要多套一层补丁文件夹。

4.照常从 Steam 启动游戏即可。不需要另外运行安装程序，也不需要填写任何密钥。

常用按键见[使用说明](README.md)。

## Steam Deck（SteamOS）

游戏原版已通过Valve的Steam Deck验证，并提供Linux原生版。本汉化包针对Windows版，尚未经过Steam Deck实机验证；下面是Proton配置参考。

1.在Steam库中打开《Elsinore》的“属性”→“兼容性”，勾选“强制使用特定Steam Play兼容工具”，选择Proton。

2.等待Steam完成Windows版游戏文件的下载或更新。退出游戏后，在桌面模式打开游戏的本地文件，把补丁全部内容解压到能看到 Elsinore.exe 的目录中。

3.在游戏“属性”→“通用”→“启动选项”中，填写下面这一整行：

    WINEDLLOVERRIDES="winhttp=n,b" %command%

4.从Steam启动游戏，检查中文是否正常显示。F8原文切换和Ctrl跳过可使用外接键盘，或通过Steam输入映射到按键。

不要把补丁直接解压到游戏的Linux原生版本目录；需先切换到Proton运行的Windows版。包内Install.cmd、Uninstall.cmd及PowerShell脚本是Windows工具，SteamOS按本节手动解压步骤操作。

## 更新旧补丁，或已安装其他模组

先退出游戏，把新版补丁完整解压到一个临时文件夹，再打开其中的 ElsinoreHan 文件夹，双击 Install.cmd，粘贴游戏目录并回车。它会先检查是否有文件冲突；成功后即可启动游戏。

出现报错请保留提示，参照[常见问题](TROUBLESHOOTING.md)处理。不要强行覆盖其他模组的文件。这个工具不会备份旧补丁，也不需要管理员权限。

## 恢复英文或卸载

只想看英文：在游戏中按 F8 即可，再按一次恢复中文。

想卸载汉化：退出游戏，打开游戏目录中的 ElsinoreHan 文件夹，双击 Uninstall.cmd，输入游戏目录并回车。

卸载工具会保留无法确认归属或被修改过的文件，以免影响其他模组。直接解压安装后卸载，可能留下通用加载器和翻译组件，这是正常情况；不要直接删除整个 BepInEx 文件夹。完成后可以自行删除 ElsinoreHan 文件夹及根目录的四份中文说明。

补丁不会备份或恢复你的存档。若需要自行备份，先退出游戏，再把下面这个文件夹复制到自己保管的位置：
%APPDATA%\Golden Glitch Studios\Elsinore
