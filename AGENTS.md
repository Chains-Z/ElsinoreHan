# ElsinoreHan 项目约定与最新交接

更新时间：2026-10-09。当前阶段：**中文初稿已安装，界面漏提修复已交付，随用户实际游玩持续校订**。本文件只保留项目特有约定、当前进展和接手必需信息；历史选型、原始统计与试译详情见任务文档。

语言、沙盒、Windows通用操作、subagent使用、Git提交和通用测试分级沿用用户级AGENTS，本文件不重复维护。

项目目标是先玩中文初稿，再随游玩校订；完整人工审校不作为开玩的前置条件。项目文档和验证记录集中在 docs/dev-tasks/localization/ 与 runtime/evidence/。

## 接手先读

1. README.md：当前安装、快捷键和入口。
2. docs/dev-tasks/localization/ui-audit.md：最新界面修复、源审计和实际验收。
3. runtime/evidence/ui-audit-verification.json：当前验证摘要；full-patch-verification.json是已被取代的初版快照。
4. docs/dev-tasks/localization/sol-full.md：冻结全文、来源、实际CLI用量与维护方式。
5. 需要追溯历史时再读 docs/dev-tasks/localization/README.md；原粗提取统计在 analysis/metrics.json，脚本为 analysis/analyze.py。

不要重复引擎识别、从零选模型或以原粗提取清单重新开始全文翻译。

## 现场与已安装补丁

- 项目：D:\MyProjects\ElsinoreHan；游戏：D:\SteamLibrary\steamapps\common\Elsinore。
- 已验证游戏：Windows x86、Mono，Unity 2018.4.20f1，《Elsinore》1.4.1（3678），主要文字组件为TextMeshProUGUI。
- 补丁结构：BepInEx 5 x86 + XUnity.AutoTranslator 5.6.2 + 中文TMP字体 + 本项目F8切换插件。词表预制离线加载；Endpoint与FallbackEndpoint均为空，不在游玩时调用翻译API。
- 当前正式词表 **16,841条**：原16,228条加界面修复新增613条。原始全文由 gpt-6.1-sol 经现有Codex登录完成112批；界面补译和源审计由本会话及subagents完成，不重跑全文。
- 共59条动态规则：24个数字/F# %s模板，35条限定UI拆分规则。MaxTextParserRecursion=64支持日期、房间、名单和多段组合；配置变更需重启游戏，Alt+R只重载词表。
- F8显示缓存的真实英文原文，再按恢复中文；不是从中文反向翻译。插件源码 tools/patch/TranslationToggle.cs。原手工sample.txt已备份停用。
- 未覆盖原游戏exe、UnityPlayer.dll、resources.assets或Assembly-CSharp.dll；四文件哈希已核对一致。
- 当前个人备份包 runtime/package/ElsinoreHan-Sol.zip 已与安装同步。依赖、字体、ZIP、游戏副本、安装/存档备份和密钥均不入Git。

## 界面提取与译文治理

- 用户截图已证明原提取漏掉短标签、资源字段及动态拼接；“清单翻完”不等于“全游戏覆盖”。不再使用最少两词或字符串长度门槛决定是否为玩家文字。
- 已审核两DLL的93,955处ldstr引用、21,516个唯一含英语源串：14,815原词表覆盖，81补译，6,560程序ID/日志/开发占位排除，60正文格式别名复用。资源审核56个TextAsset、12个序列化文件、51,173处字段，467个唯一漏提源串已补译。
- 完整判断、owner/IL偏移、对象pathID与字段来源在 analysis/ui-audit/；原始重复引用和人工检索中间件被忽略，复现脚本保留。
- 房间显示名来自 RoomMarker.playerFacingName；物件来自 ObservableSceneObject.ObjectName；按钮还有tooltip字段。names.locations/observables是内部标记，不能直接翻。
- 界面显示值不等于枚举名，例如Faster对应Fast，Fullscreen对应Full。设置必须按真实显示值逐档检查，不能只验证当前档位。
- 时间线/教程/结果通过格式器拼接。先审核实际源片段和组合语法，再用限定规则消费译文；人物与房间使用真实白名单，不全局替换程序标识或泛化英文分词。上游Splitter按后加载优先；.NET普通$可能在末尾换行前匹配，新增UI规则使用严格末尾锚点。
- 13首片尾歌曲保留作品原名；真实工作人员姓名、技术品牌、按键名按实际语境保留。内部条件、动作/音效ID和日志不作为玩家译文。
- 冻结源输入、raw、outputs和审计在 translation/sol-full-2026-10-09/。保留原始响应及字节哈希，不覆盖raw，不重译已通过批次；.gitattributes已对冻结目录禁用换行转换。
- 正文修订记录放 local-corrections.json；新界面补译放 translation/supplemental/ui-translations.json，规则放 dynamic-ui-rules.json。已有源词覆盖必须记录准确previous_target，保留来源与source_sha256。60个正文别名只复用旧译文，其中24个仅补外层斜体。
- 文风使用自然易读的现代中文，仅保留原文已有的古雅、戏剧感和人物差异；不统一文言化、不补写关系/动作/情绪。人物身份以本游戏为准，忠实保留否定、时间、条件和推测程度。

## 验证与存档保护

- 当前验收运行：17da6bd3fa514b03ad5c3e82ca529713。16,841条实际字典解析、24个格式消费者、29个递归消费者用例、48个真实游戏缓存用例通过；13种设置值逐档中文/F8往返/组件溢出检查通过，合计19项游戏组件断言，2,816个汉字覆盖通过。15项翻译/导出回归、11项探针回归通过。
- 后台组件/缓存验证不等于物理F8按键注入、像素渲染或完整游玩E2E。全剧情分支、图片文字、未知动态兜底及对白/资料像素排版仍可能需要用户反馈；不得宣称所有界面零漏译。
- 游戏测试不得抢前台或发声。现有入口使用隐藏 -batchmode -nographics -nosound、低优先级和10FPS，确认Wwise暂停并监测窗口；出现窗口或超时就终止自己启动的进程，不回退全屏测试，不要求用户手动截图作为前置条件。
- 用户在玩时使用 runtime/game-test/settings-options 独立游戏副本，按可执行文件路径区分进程；不关闭或操作用户原游戏。安装脚本要求目标游戏关闭，不绕过保护覆盖运行中的插件。
- 测试先复制真实存档到 runtime/backups/probe-save-*；RuntimeProbe在业务初始化前重定向SaveLoad.SaveFileDirectory，拦截SaveData与旧版迁移。保护建立失败直接终止，避免普通退出再次保存。前后核对原存档文件哈希、修改时间和数量。
- 设置逐档测试只改克隆配置并点取消，不点击确认或应用。真实暂停动作进入菜单，不能仅强行激活Canvas后误报导航成功。
- 临时RuntimeProbe不打包给用户，finally清理插件/appid并确认测试进程退出。实际存档路径为 %APPDATA%\Golden Glitch Studios\Elsinore。
- 修复前一次诊断曾自动加载旧进度并在退出时写回game.save，旧备份未保留，进度差异未知，已告知用户。记录见 docs/dev-tasks/localization/save-write-incident.md；后续隔离通过不代表此前存档未变。

## 维护入口与下一步

- tools/translation/prepare_ui_supplement.py：从审计与既有译文生成补译/规则；只在要更新这组来源时运行，避免覆盖未整理的人工修订。
- tools/translation/export_sol_full.py：核对冻结结果、修订及补译后导出正式词表。
- tools/patch/install-full.ps1：游戏关闭后备份安装；tools/patch/package-full.ps1：按白名单生成个人备份ZIP。
- tools/patch/run-toggle-probe.ps1：默认菜单/F8后台验证；逐档模式使用 ELSINOREHAN_PROBE_SETTINGS_OPTIONS=1，并设置正式译文、字形、冻结缓存用例路径。详细运行契约见源码与ui-audit.md。
- 下一步按用户实际遇到的漏译、错译和排版反馈修订。优先确认源字段、实际组合及拦截路径；不要重译全文作为修补方法。
- 公开分享尚未完成：当前arialuni_sdf_u2018字体的再分发许可未核实，正式发布应换授权明确且兼容Unity2018/TMP的字体并验证，补齐第三方许可、安装/卸载说明和干净目录安装验证。当前ZIP是个人备份，不称正式公开发布包。
- 百炼四模型比较已停止，旧结果只作历史证据，不恢复调用、不要求新Key。公开业务空间地址在 translation/provider.json，密钥仅在被忽略的api-key.txt，不输出或打包。套餐实际CLI用量见sol-full.md，不能从token数编造周额度扣减百分比。

历史参考 PipistrelloHan 的实现差异与翻译工具调研保存在任务文档；其IL2CPP/BepInEx6/多语言CSV方案不能直接套入本游戏Mono x86现场。
