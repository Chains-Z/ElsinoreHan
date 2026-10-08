# 界面英文漏提与动态组合修复

2026-10-09，用户实际游玩截图发现设置非当前档位、房间/物件/按钮悬停提示、教程和时间线大量英文。问题确认是提取范围与运行消费漏项，不能将原有16228条清单翻完称作全游戏文字覆盖。

当前修复已安装到原游戏目录，个人备份ZIP同步更新；共 **16841条词条**，在原16228条基础上新增 **613条**，另有5个已有源词补修/复核（含Normal→正常）。正常重启游戏生效；这次增加MaxTextParserRecursion配置，Alt+R只重载词表，不能替代配置首次重启。

## 完整源审计

程序集两DLL的所有ldstr不设词数/长度门槛，记录真实引用、owner和IL偏移：

| 项目 | 数量 |
| --- | ---: |
| 实际IL引用 | 93955 |
| 唯一含英文字母源串 | 21516 |
| 原词表已覆盖 | 14815 |
| 需补UI源串 | 81 |
| 程序ID、动作/音效、日志或开发占位排除 | 6560 |
| 与既有正文仅斜体/破折号有差异、复用原译 | 60 |

资源审核56个TextAsset、12个序列化文件、51173处字段，补齐467个精确唯一源串，其中285条事件描述、30个房间名、64个物件标签、12个按钮提示。已保留逐字段来源、对象pathID、偏移和显示消费者；内部ID、名字标记、字体/Wwise/Rewired技术数据不当作玩家文字。13首片尾歌曲保留作品原名，真实工作人员姓名和技术品牌也保留。

完整记录在 [analysis/ui-audit/](../../../analysis/ui-audit/)，不是只靠截图逐句补词。assembly-summary.json、resource-summary.json提供判断统计；对应strings/candidates/exclusions保存全文源证据。原始重复IL和检索中间件保留本机，不进入Git。

## 成因与修复

原粗提取既使用了两词门槛，也只处理部分JSON资源和指定字段；漏掉schedule.description、人物subtitle、宠物名、房间RoomMarker.playerFacingName、ObservableSceneObject.ObjectName和按钮tooltip。names.locations/observables实际是内部标记，不能直接翻。

文字速度显示Normal/Faster/Fastest/Instant，而枚举名有Fast；屏幕显示Fullscreen，内部枚举是Full。现在按真实显示方法补齐13种文字值，含无边框分辨率Native。音量和分辨率数字不翻。

动态界面追加日期、房间bullet、事件前缀、富文本段落、人物名单和结果句式。当前有24个数字/F# %s模板与35条限定UI拆分规则，共59条。房间和人物采用实际白名单，参数递归消费预制译文；未知谓词/程序ID不会被全局词语替换。既有112批全文输出及raw未改写，60个正文格式别名只复用旧译文，24个别名增加外层斜体。

上游默认MaxTextParserRecursion=1只能消费一层，导致拆分后仍留英文；当前设64以容纳有限人物名单和多段文本。上游RegexSplitter按后加载优先，验证器已与真实顺序一致；新增UI规则使用.NET严格末尾锚点，避免普通$在末尾换行前匹配而丢换行。

源码入口：prepare_ui_supplement.py从审计与固定词表制备补译；export_sol_full.py合并补译与规则，拒绝无来源、哈希不符、未记录旧值的覆盖。补译与规则保存于 [translation/supplemental/](../../../translation/supplemental/)。本会话及subagents补审/补译，不再调用百炼，不重跑全文CLI。

## 实际验证

最终真实游戏运行：17da6bd3fa514b03ad5c3e82ca529713，在runtime/game-test/settings-options独立副本使用真实存档的隔离副本。原游戏正在运行时也不关闭或操作其窗口；最终安装时原游戏已关闭。后台-nographics/-nosound、隐藏、低优先级和10FPS，保存/迁移拦截继续启用；原存档哈希与修改时间不变。

- 16841条实际XUnity字典解析逐条通过。
- 59条真实Splitter构造，24个格式消费者通过；29个递归消费者用例通过，含普通对白/多余房间后缀不误匹配的负例。
- 实际游戏ITranslator缓存48个冻结用例全部精确匹配，包括旧长资料、新房间/物件/按钮文字、日期、未来事件、教程、时间线与结果。
- 真实设置页签与左右按钮回调逐档遍历13种文字值，中文/F8原文/恢复、active与溢出标志全部通过。只改设置页临时克隆、点取消，未确认或应用配置。
- 19项游戏组件断言全部通过，2816个所需汉字覆盖通过。
- 15项翻译/导出回归、11项探针回归通过；防止只验证当前选项或仍显示Faster时误报。
- 原游戏四个文件哈希不变，临时探针/进程已清理。ZIP词表及F8插件与实际安装逐文件一致。

摘要：[ui-audit-verification.json](../../../runtime/evidence/ui-audit-verification.json)。逐档记录：[ui-audit-settings-options.txt](../../../runtime/evidence/ui-audit-settings-options.txt)。安装备份：runtime/backups/full-17f41047d9554d668e34e81aa0df96f9。

这些是实际游戏组件和缓存集成检查，不是全剧情分支或像素渲染E2E。未知动态逻辑兜底、图片文字、未覆盖类型仍可能需要实际游玩反馈，不能再次用清单完整性宣布所有界面零漏译。此前诊断存档事故及后续隔离修复继续保留在save-write-incident.md；本次不抹去此前发生的写入。当前ZIP仍为个人备份，公开分发字体授权与完整第三方许可整理另行处理。
