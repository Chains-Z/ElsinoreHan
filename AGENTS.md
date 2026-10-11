# ElsinoreHan 项目约定

《Elsinore》的离线中文补丁，先提供可玩的中文初稿，再随实际游玩定向校订。游戏为 Windows x86、Unity 2018.4.20f1、Mono，主要使用 TextMeshProUGUI；补丁采用 BepInEx 5、XUnity.AutoTranslator、中文TMP字体和本项目F8兼容插件。

语言、沙盒、Git提交和通用测试规则沿用用户级AGENTS。项目位于 `D:\MyProjects\ElsinoreHan`，游戏位于 `D:\SteamLibrary\steamapps\common\Elsinore`。

## 文档与维护入口

- 开始任务时先读 [交接文档的当前状态](docs/dev-tasks/localization/handoff.md#当前状态)，实现细节按任务需要查阅。
- [README.md](README.md) 面向仓库读者，说明用途、使用方式和开发入口；进展、版本号、统计、哈希及安装历史写入 `docs/dev-tasks/localization/` 和 `runtime/evidence/`，不追加到本文件。
- `tools/translation/export_sol_full.py` 导出词表；`tools/patch/install-full.ps1` 备份安装；`tools/patch/package-full.ps1` 按白名单打包。候选包使用 `-PendingInstall`，安装后再生成已安装包；区分候选与正式安装证据，保留旧阶段快照。

## 翻译与运行约束

- 根据实际反馈定向修复，先确认真实源字段、角色语境、运行变体和拦截路径。不要重新识别引擎、从零选模型、重译全文或恢复已停止的模型比较。
- 使用自然易读的现代中文，保留原文的戏剧感和人物差异；不补写关系、动作、情绪或未明确的指代，忠实保留否定、时间、条件和推测程度。人物身份以本游戏为准，既有术语决定见交接文档。
- 保留原文斜体、粗体、占位符及必要换行，不全局互换强调格式。
- `translation/sol-full-2026-10-09/` 的输入、raw、outputs和审计保持冻结。正文校订通过 `local-corrections.json` 的 `apply_at_export` 或既有专项校订层应用；界面补译与规则放在 `translation/supplemental/`。覆盖已有源词必须记录准确旧值、来源和 `source_sha256`，别名须复用经治理的译文。
- 提取玩家文字不设最少词数或长度门槛；内部标识、程序日志和音效ID不作为译文。动态拼接使用真实白名单和限定规则，核查实际显示值，勿直接翻枚举名或泛化英文分词。
- 保持真实XUnity逆序首匹配和递归上限64；规则失败时不得在验证器中改选其他规则兜底。新增规则注意完整斜体数字模板和严格末尾锚点。
- 游戏中只加载预制离线词表，`Endpoint` 与 `FallbackEndpoint` 均为空。F8显示缓存的真实英文原文，中文不得写入游戏原始业务数据；完整组合须进入XUnity内存缓存。配置变更需重启，Alt+R只重载词表。
- 原游戏exe、`UnityPlayer.dll`、`resources.assets`、`Assembly-CSharp.dll`不得被补丁覆盖。依赖、字体、ZIP、游戏副本、备份和密钥不入Git；不输出或打包密钥。

## 验证、存档与安装保护

- 按变更范围运行相关消费者、治理检查和必要页面验证，不重复未改变的重型验收。组件、离线API、资源重放、字体网格均须按实际层级报告，不称物理按键、像素或完整剧情E2E通过。
- 游戏测试使用独立副本、隐藏 `-batchmode -nographics -nosound`、低优先级和10FPS，确认Wwise暂停并监测窗口；出现窗口或超时立即终止自己启动的进程，不抢前台、不发声、不回退全屏测试。
- 测试先克隆真实存档，在业务初始化前重定向 `SaveLoad.SaveFileDirectory`，拦截保存和旧版迁移。保护失败立即终止，避免普通退出写回；前后核对原存档哈希、修改时间和数量。实际存档位于 `%APPDATA%\Golden Glitch Studios\Elsinore`。
- 按可执行文件路径区分测试副本和用户游戏，不关闭或操作用户原游戏。安装前确认目标游戏已退出，通过安装器备份安装，不绕过运行保护。
- 临时探针、输入/分辨率保护和appid不打包；在finally恢复入口与配置的原始字节、清理临时文件并确认测试进程退出。设置测试只改克隆配置并取消，不应用到用户配置；导航须经过真实业务入口。
- 涉及探针、TMP/F8、日志或动态UI时，先查交接文档中的实现注意事项及对应任务文档，遵守真实签名、初始化、状态转换和来源契约。
- 当前ZIP仅为个人备份。公开发布前核实字体再分发许可，补齐第三方许可、安装/卸载说明和干净目录安装验证；不将个人包称为正式公开发布包。
