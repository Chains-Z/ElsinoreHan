# ElsinoreHan

《Elsinore》的离线中文汉化项目，包含预制译文、文字提取与校验工具，以及用于中文TextMeshPro显示和F8原文切换的兼容插件。译文结合实际游玩反馈持续校订。

翻译：GPT-6.1-sol；校对：GPT-6.1-sol 与项目作者（Chains-Z）。

已经人工游玩所有路线，应该没有重大翻译错误，但不代表已穷尽所有已知对白，也不保证每句对白都经过逐句校对。仍欢迎反馈错译、漏译和显示问题。

游戏运行时直接读取本地词表，不调用翻译API，也不需要API Key。补丁通过加载器工作，不覆盖游戏原始资源或程序集。

## 汉化声明

本汉化补丁为民间无偿汉化，免费发布，仅作学习交流使用。请支持正版游戏。

项目作者保留其依法享有的翻译及校订成果权利。未经许可，不得将本项目自有译文及校订成果用于商业用途，也不得擅自修改后重新打包发布。原样转载本项目发布的汉化包时，请注明作者 Chains-Z 及项目来源，并保留本声明及文件完整性。

上述译文及原包转载声明不限制 LGPL-2.1-or-later 授权的代码与技术文档，也不改变第三方组件和字体的原有许可。相关代码可以依其许可证修改、用于商业用途及再分发；欢迎通过项目仓库提交改进与译文修正。游戏原文及原作的权利归相应权利人所有。

完整授权范围见 [LICENSE-SCOPE.md](LICENSE-SCOPE.md)。

## 功能与适用版本

- 翻译对白、人物资料、文档、线索、日志、地图及时间线等玩家文字，并处理运行时拼接。
- 使用基于思源黑体生成的中文TMP字体，保留原文的粗体与斜体。
- 按 **F8** 在当前文字的英文原文与中文译文之间切换。
- 演职人员名单播放时，长按左右任意 **Ctrl** 约 1 秒即可跳过，保留原有空格快进。
- 按 **Alt+R** 重载词表；修改加载器配置后需要重启游戏。

适用于Windows版《Elsinore》1.4.1（3678），支持64位Windows。游戏程序为x86，使用Unity 2018.4.20f1、Mono。补丁使用BepInEx 5 x86、XUnity.AutoTranslator 5.6.2和本项目兼容插件；其他平台、游戏版本和加载器组合尚未验证。

## 使用与安装

可安装的完整补丁从 [GitHub Releases](https://github.com/Chains-Z/ElsinoreHan/releases) 下载。保存并退出游戏，将补丁ZIP中的所有内容解压到 `Elsinore.exe` 所在目录，再正常从Steam启动即可，不需要运行额外脚本。压缩包根目录的“安装方法.txt”“使用说明.txt”“常见问题.txt”“更新说明.txt”可直接双击阅读。详细步骤与可选冲突检查、卸载工具见 [玩家安装说明](docs/release/INSTALL.md)。已有其他模组时先查看说明，避免直接覆盖共用加载器。

本仓库保存源码、译文和核验记录；游戏本体、玩家存档、第三方二进制、字体与ZIP不纳入Git，克隆仓库不会得到完整运行包。Release附件单独提供经过白名单与敏感信息检查的运行组件、许可和必要对应源码。

已有补丁的游戏正常从Steam启动即可。遇到疑句时按F8查看英文；报告问题时附上原句、截图和场景或说话人，有助于定位实际运行源文。

维护者更新已有安装时，先准备好本地依赖及候选包，保存并退出游戏，然后在仓库根目录的PowerShell中执行：

```powershell
./tools/patch/install-full.ps1 -GamePath 'D:\SteamLibrary\steamapps\common\Elsinore'
```

`-GamePath` 可替换为实际游戏目录。安装器核对词表、插件及字体的验收哈希，再更新词表、中文字体、许可、兼容插件和配置，不保留旧补丁备份。安装结果写入 `runtime/evidence/full-installed-files.json`。

此脚本供维护者更新已配置好加载器的环境，要求目标已有 `BepInEx/config/AutoTranslatorConfig.ini`；玩家首次安装直接使用Release完整包。公开包的打包入口为 `tools/release/build-public-release.py`，需要本地已验证运行包和许可审计材料，详见 [公开发布工作记录](docs/dev-tasks/public-release/README.md)。

### 停用与回退

退出游戏后，可将游戏目录 `doorstop_config.ini` 的 `[General]` 节中 `enabled` 改为 `false`，再次启动时停用加载器；改回 `true` 可恢复。此操作会停用通过同一加载器加载的其他插件。

退出游戏后，可使用公开包 `ElsinoreHan/Uninstall.cmd` 卸载，具体边界见 [卸载说明](docs/release/INSTALL.md#恢复英文或卸载)。直接解压没有安装归属记录，工具只移除准确匹配的本项目独有文件，保留共用加载器和其他模组；通过辅助安装器安装时按归属记录处理，仍保留用户修改内容及其他模组需要的环境。

回退某次更新时，可保留相应Release完整包，或从Git取得对应源码和校订数据，使用本机依赖重新导出、构建、验证。Git不包含字体、第三方依赖或个人存档，不能恢复这些文件；项目不自动积累旧补丁备份。后台测试使用临时隔离存档，结束后清理。

## 开发与校订

从 [AGENTS.md](AGENTS.md) 了解修改约束，从 [维护交接](docs/dev-tasks/localization/handoff.md) 查看当前安装、待安装候选和相关实现入口。

译文在 [translations.json](translation/sol-full-2026-10-09/translations.json) 中可检索。原始模型输入、响应与输出保持冻结；修改通过有来源、源哈希及准确旧值的校订层应用，新增界面译文与动态规则位于 `translation/supplemental/`。

词表导出与导出器单元检查使用Python 3；插件编译使用Windows的 .NET Framework C# 编译器，并依赖游戏Managed程序集及本地 `runtime/vendor/` 中的BepInEx、Harmony和XUnity文件。调用资源提取的Python脚本还需要 `pefile`。构建脚本的默认游戏路径为 `D:\SteamLibrary\steamapps\common\Elsinore`。

在依赖齐全的维护环境中，常用命令如下：

```powershell
# 应用校订并核对冻结来源，生成离线词表
python tools/translation/export_sol_full.py

# 运行导出器单元检查
python -m unittest discover -s tools/translation -p test_export_sol_full.py

# 编译兼容插件，可用 -GamePath 指定游戏目录
./tools/patch/build-toggle.ps1

# 生成尚未安装的个人候选包
./tools/patch/package-full.ps1 -PendingInstall
```

导出器会更新生成词表和核验记录。对白、动态组合或插件变化还需运行对应的消费者与组件检查；工具选择和后台游戏测试注意事项见 [维护交接](docs/dev-tasks/localization/handoff.md#生成与验证工具)。

中文字体通过本游戏Unity2018的字体引擎生成，使用思源黑体SC Regular作为源字体。构建还需要 `fontTools` 和 `UnityPy`；字符集、生成、装配及加载验收步骤见 [字体构建说明](docs/dev-tasks/localization/font-replacement-2026-10-11.md)。

## 目录

| 路径 | 内容 |
| --- | --- |
| `tools/translation/` | 译文导出、来源审计、校订生成与验证工具 |
| `tools/release/` | 公开包白名单构建、辅助安装与保守卸载工具及测试 |
| `docs/release/` | 玩家安装、故障排查、版本及发布说明 |
| `tools/patch/` | TMP/F8插件源码、构建、安装、打包及后台探针 |
| `translation/sol-full-2026-10-09/` | 冻结全文、原始响应、合并译文与导出核验 |
| `translation/supplemental/` | 补译、定向校订、动态规则与回归用例 |
| `analysis/` | 文字提取与界面来源分析 |
| `docs/dev-tasks/localization/` | 实现说明、维护交接、任务及历史记录 |
| `runtime/evidence/` | 验证与安装核验摘要 |
| `licenses/` | 加载器、翻译组件、字体及TMP组件的完整许可与对应源码说明 |
| `runtime/vendor/`、`runtime/package/`、`runtime/backups/` | 本机依赖、个人补丁包及备份，不入Git |

## 已知限制与许可

初稿与自动检查不能保证所有剧情、未知动态组合或图片文字均已覆盖；部分对白和长文档的实际屏幕排版仍需随游玩确认。后台组件或字体网格检查不代表完整游玩及全场景像素验收。

本项目原创插件、工具脚本及配套技术文档采用 **LGPL-2.1 或更高版本** 发布，完整条款见 [LICENSE](LICENSE)，适用范围见 [LICENSE-SCOPE.md](LICENSE-SCOPE.md)。游戏原文、译文及剧情数据不属于该代码许可证的授权范围；第三方组件和字体分别遵守各自许可。

欢迎通过 Issue 反馈问题，通过 Pull Request 提交代码改进和译文修正，方便大家共享维护成果。LGPL允许商业使用和收费分发，也不强制修改者把代码提交到本仓库；分发相关修改时仍须履行对应源码等许可义务。贡献回本仓库是我们的协作倡议。

BepInEx、XUnity和Harmony遵循各自的许可。中文字体来自Adobe官方思源黑体，按 [SIL Open Font License 1.1](licenses/ElsinoreHanSans-OFL.txt) 使用和再分发；派生资源名称为 `ElsinoreHan Sans SDF`，来源与TMP组件许可见 [字体说明](licenses/ElsinoreHanSans-NOTICE.txt)。补丁包附带这些许可文件。

完整第三方许可及源码索引见 [THIRD-PARTY-NOTICES.md](licenses/THIRD-PARTY-NOTICES.md)。公开包随附本项目插件及Doorstop的对应源码归档、构建说明和完整许可，源码不含游戏程序集。干净目录解压、实际加载、中文／英文切换和卸载验证记录见 [公开发布验收](docs/dev-tasks/public-release/verification.md)。

公开Git仓库保存源码、译文与审计资料，不上传本机API Key、字体文件、游戏本体、存档、下载依赖或安装包。Release附件仅按许可分发白名单运行组件，不包含游戏和个人数据。历史字体名称和许可核查文档仅记录研究过程，不表示仓库包含这些字体。
