《Elsinore》离线中文补丁的首个公开版本，汉化补丁版本为 **1.0.0**，内部版本为 **1.5.15**（兼容插件）；两者独立编号。适用于 Windows 版《Elsinore》1.4.1（3678），支持 64 位 Windows，需要自行拥有并安装游戏。

## 安装

1.保存进度并完全退出游戏，下载 [ElsinoreHan-v1.0.0-windows.zip](https://github.com/Chains-Z/ElsinoreHan/releases/download/v1.0.0/ElsinoreHan-v1.0.0-windows.zip)。

2.将 ZIP 中的所有内容直接解压到 `Elsinore.exe` 所在目录，保持目录结构，不要额外套一层文件夹。

3.正常从 Steam 启动游戏，按 **F8** 在中文与英文原文之间切换。

演职人员名单播放时，长按左右任意 **Ctrl** 约 1 秒即可跳过；原有空格快进仍可使用。

运行时只读取本地译文，不调用在线翻译 API，也不需要 API Key。**Alt+R** 可重载本地词表；更新补丁、字体或配置后请重启游戏。

已有其他模组或更新旧补丁时，建议先将 ZIP 解压到外部目录，用其中 `ElsinoreHan/Install.cmd` 检查冲突。压缩包根目录提供可双击阅读的“安装方法.txt”“使用说明.txt”“常见问题.txt”“更新说明.txt”；也可查看[本版安装说明](https://github.com/Chains-Z/ElsinoreHan/blob/v1.0.0/docs/release/INSTALL.md)与[故障排查](https://github.com/Chains-Z/ElsinoreHan/blob/v1.0.0/docs/release/TROUBLESHOOTING.md)。

## 内容与限制

翻译：GPT-6.1-sol；校对：GPT-6.1-sol 与项目作者（Chains-Z）。

已经人工游玩所有路线，应该没有重大翻译错误，但不代表已穷尽所有已知对白，也不保证每句对白都经过逐句校对。

本版包含 17,069 条预制词条和 157 条动态文字规则，涵盖对白、人物资料、文档、日志、线索、地图和时间线等文字，并提供中文字体与中英文切换功能。

译文以机器翻译初稿为基础，已结合实际游玩持续校订，尚未对所有分支逐句人工校对。未知动态文字、图片文字和部分长文排版仍可能存在遗漏；其他系统、游戏版本及模组组合尚未验证。工作人员姓名、歌曲名、品牌和按键等部分内容按原文保留。发现问题时请附中英文截图、说话人或界面及复现步骤，公开反馈请标明剧透。

补丁不包含游戏本体、玩家存档或存档恢复功能，不替换游戏原始可执行文件和资源文件。

## 文件校验、许可与源码

下载后可使用本页附件 [SHA256SUMS.txt](https://github.com/Chains-Z/ElsinoreHan/releases/download/v1.0.0/SHA256SUMS.txt) 核对 ZIP 的 SHA-256。

本项目原创插件、工具脚本及配套技术文档采用 **LGPL-2.1 或更高版本**，完整许可和范围说明随包提供，仓库中见 [LICENSE](https://github.com/Chains-Z/ElsinoreHan/blob/v1.0.0/LICENSE) 与 [LICENSE-SCOPE.md](https://github.com/Chains-Z/ElsinoreHan/blob/v1.0.0/LICENSE-SCOPE.md)。游戏原文、译文及剧情数据不属于该代码许可的授权范围，第三方内容遵循各自许可。

欢迎通过 Issue 和 Pull Request 贡献修正。LGPL允许商业使用及收费分发，不强制把修改提交到本仓库；分发相关修改时仍须遵守提供对应源码等要求。

包内 `ElsinoreHan/licenses/THIRD-PARTY-NOTICES.md` 提供第三方组件与许可索引。`ElsinoreHan/sources/ElsinoreHan-1.5.15-source.zip` 包含本项目插件全部编译源文件、原构建脚本、许可和构建说明；`ElsinoreHan/sources/UnityDoorstop-4.5.0-source.zip` 另附Doorstop对应源码和构建脚本。[本版项目源码与译文维护资料](https://github.com/Chains-Z/ElsinoreHan/tree/v1.0.0)另见版本标签。
