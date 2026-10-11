# 汉化维护交接

更新时间：2026-10-12。本文维护当前状态、实现注意事项和记录入口；长期执行约束见 [AGENTS.md](../../../AGENTS.md)，仓库介绍和使用方法见 [README.md](../../../README.md)。每次修改在对应任务文档记录详情，完成安装后再更新本页的正式安装状态。

## 当前状态

| 项目 | 状态与依据 |
| --- | --- |
| 维护阶段 | 中文初稿已可玩，继续根据实际游玩反馈定向校订，不等待全分支人工审校 |
| 正式安装 | 插件1.5.3，17,041词条，155动态规则；[安装核验](../../../runtime/evidence/offline-log-cache-install-verification-2026-10-12.json)；日志缓存重建修复见[本轮记录](othello-log-followup-2026-10-12.md) |
| 最新对白校订 | 幽灵“一场更大的游戏”、贝尔纳多“至少，我还有你这个朋友”、奥赛罗“苏丹麾下的一名高级大臣”均已安装；“抓住你的脑袋”按用户决定保留，见[奥赛罗术语核查](othello-term-review-2026-10-11.md) |
| 个人备份包 | `runtime/package/ElsinoreHan-Sol.zip` 与40文件包目录及38运行文件一致；已换新字体并附3份许可/说明，无旧Arial字库；当前哈希见最新安装核验 |
| 安装备份 | `runtime/backups/full-1102ff802f4944258cb6846073d5cea5`，8个旧补丁文件核对成功；`full-installed-files.json` 指向正式1.5.3安装 |
| 安装保护证据 | 原游戏四文件及8个存档的哈希、修改时间、大小和数量未变；字库、词表、许可字节不变，配置解码文本逐字相同，未启动主游戏 |
| 发布状态 | 仅供个人备份；思源字体再分发许可与TMP组件许可已附，其他依赖许可、完整卸载说明与干净目录安装验证仍待完成 |
| 当前字体 | `ElsinoreHan Sans SDF`，来自思源黑体SC Regular 2.005R，OFL1.1；7,660字形及实际运行纹理与原生生成结果一致，“沉”上横检查通过；[字体替换及验证](font-replacement-2026-10-11.md)、[授权争议复核](font-license-risk-check-2026-10-11.md) |

下一步继续处理用户反馈。安装候选时先确认用户游戏已退出，使用安装器备份安装，再生成不带 `-PendingInstall` 的包并记录新证据；不要重跑未改变的重型页面验收。

## 接手入口

| 任务 | 首选资料 |
| --- | --- |
| 最新游玩校订、通知/分享/信息正文修复 | [1.5.1跟进](playthrough-followup-2026-10-11.md)、[更大的游戏](larger-game-followup-2026-10-11.md) |
| 通知名单、人物简介组合、文档F8 | [阅读界面跟进](reading-followup-2026-10-10.md) |
| 文章与人物口语审校 | [阅读正文](reading-text-review-2026-10-10.md)、[伊尔玛](irma-dialogue-review-2026-10-10.md)、[其他角色](dialect-dialogue-review-2026-10-10.md) |
| 日志组合与滚动位置 | [混合日志](mixed-log-followup-2026-10-10.md)、[日志跟进](log-followup-2026-10-10.md) |
| 最新日志缓存修复、字号核查 | [奥赛罗日志](othello-log-followup-2026-10-12.md)、[候选证明](../../../runtime/evidence/offline-log-cache-verification-2026-10-12.json) |
| 线索、地图、时间线、界面提取 | [UI跟进](ui-followup-2026-10-10.md)、[源审计](ui-audit.md) |
| TMP兼容与字体 | [思源字体替换](font-replacement-2026-10-11.md)、[TMP兼容](tmp-compatibility.md)、[运行界面跟进](runtime-ui-followup.md) |
| 冻结全文、来源与实际CLI用量 | [Sol全文](sol-full.md) |
| 存档事故与防护依据 | [存档写入事故](save-write-incident.md) |
| 更早的研究与阶段记录 | [历史索引](README.md)、[原AGENTS交接内容迁移快照](handoff-history-2026-10-11.md) |

任务文档中的“当前”“已安装”等描述可能属于历史阶段。判断现状以本页及所链接的最新安装/候选证据为准，旧核验JSON保持快照，不改写成新结果。

## 已确认的术语与语境

- `Gerta` 是乔特鲁德的昵称，译为“格尔塔”；正式全名仍为“乔特鲁德”。`Playmaster` 统一为“戏剧大师”，两人的相关称号统一为“骑士卫队”。
- 用户最终保留“提婆／阿修罗”；`religious-term-reviewed.json` 只记录决定，不加载为校订层，曾改为“天神”的两处已恢复。
- 布莉特p09190保留“长期预约在这里闲待”的夸张幽默；p03368的 `both of them` 指克劳狄斯和哈姆雷特，真实分支中两人已死，不改为未来条件。
- 福丁布拉斯简介明确“与丹麦王室重修于好”。裸源 `I do.` 的共同肯定答复为“是的。”；幽灵的斜体源承接时间循环，译为“是的，我也一样。”。`bloody deeds` 不补写施暴者或受害者。
- 未来 `ImpossibleEvent` 标签为“当前条件下不会发生”，过去未发生项按过去时处理。奎因斯演出回顾使用回顾语气，不补演出时点。
- 奥赛罗 `vizier` 按用户指定译为“苏丹麾下的一名高级大臣”，不是首相；`grab your head` 保留“抓住你的脑袋”及斩首呼应，不把调情双关的推断写成具体动作。
- 13首片尾歌曲、真实工作人员姓名、技术品牌和按键名按实际语境保留。英文强调用途不代表统一强弱等级，依据见 [标记审计](english-markup-audit.md)。

## 实现注意事项

### TMP、缓存与F8

TMP1.4.0的 `SetText` 只写解析缓冲区，getter读取旧 `m_text`。插件在StringBuilder和字符串双参数入口转交原文到text setter；即时路径不拆分，setter前缀通过纯离线API消费，并登记完整组合内存缓存（`Full/scope=-1/persist=false`）。只查 `TryTranslate` 不能保证组合已缓存。源码为 `tools/patch/TranslationToggle.cs`。

1.5.3对 `LogCanvas` 单独从文件词表和真实首匹配Splitter完整重建，再准确覆盖此源内存项；不信任主API可能返回的部分译文或既有混合Full缓存。Alt+R失效重载；未知源重建返回null，上游仍可处理，不能宣称整个管线拒绝未知混合。其他页面保留原路径。当前空替换表、数字模板关闭的配置已验证，不泛化任意可选XUnity配置。

人物Title使用单行自适应字号。`LogScrollAnchor` 只保护F8，不能锁住平时滚动；长段内部并非逐词定位，结构或历史变化时保守跳过。当前思源字体合成斜体剪切设为5；旧Arial兼容分支仍为10。参数不是角度，新字体沿用10会导致样本网格相邻边界重叠。TMP1.4迁移旧序列化字段时不能恢复原生SDF8，插件在新字体读取后精确设回SDF8。

### 源字段与动态组合

房间显示名来自 `RoomMarker.playerFacingName`，物件来自 `ObservableSceneObject.ObjectName`，按钮还需查tooltip；`names.locations/observables` 为内部标记。设置显示值不同于枚举名，例如Faster对应Fast、Fullscreen对应Full。

对白运行源须遵守编译器九步破折号替换及幽灵外层斜体契约。文档运行别名见 `runtime-closeup-translations.json`，哈姆雷特简介别名见 `hamlet-bio-alias.json`。通知已有双引号保留，无引号分支不补引号；尾LF别名逐字复用正文。完整斜体数字提示须交给原数字模板，通用斜体封套不能抢先剥掉格式。

日志简称复现真实 `FormatShortCharacterName` 的第二词规则及Rosie/Guilda特判，唱词斜体不能误作舞台条目。八条一组批处理用于控制递归深度；日志验收按全部 `LOG_ENTRY` ID绑定，不把标题算作历史。

### 后台探针与真实导航

测试副本为 `runtime/game-test/settings-options`。默认 `Application.cctor` 入口可能晚于分辨率应用，临时保护需在 `GameInitialization.Awake` 前加载并跳过测试副本显示质量/分辨率应用。Rewired后台输入可能自动关闭资料，临时阻断按钮/轴查询并禁用自动输入模块；阻断次数不等于物理按键数，Unity按键和正式F8并未全部隔离。

暂停与Journal导航是 `DeferredAction`，拒绝后清队列且不自动重试；须等待真实初始化、准入及转换状态，并确认具体请求已消费。文档入口必须传非空 `onDone`，真实 `OnClosed` 无条件调用。`COLLECTED` 不代表断言成功。

`ELSINOREHAN_PROBE_JOURNAL=1` 与设置逐档模式互斥；UI_FOLLOWUP同时开启JOURNAL并提供LEAD_CASES。时间线 `loop=0` 为当前，历史索引向过去递增，Previous加1、Next减1，时钟纪元为06:00。反射使用准确签名，未参加/未来项不提前调用Details，缺scene明确跳过，不能造零Changes。

字体网格使用真实参数和冻结译文，隔离样本关闭换行/裁切，只比较glyph包络；本轮额外核对完整运行时纹理、7,660字形坐标及“沉”的固定笔画区域，仍不代表完整页面像素验收。JsonUtility会漏动态探针的嵌套数组，必须显式导出并核对完整证据。通知门禁的消费者证据须匹配当前夹具/规则哈希，旧阶段快照不改写；需要时真实重跑，并通过 `ELSINOREHAN_PROBE_NOTIFICATION_EVIDENCE` 明确传入新证明。

## 生成与验证工具

| 入口 | 用途与注意事项 |
| --- | --- |
| `prepare_ui_supplement.py` | 仅在更新其来源时运行，避免覆盖未整理的人工修订 |
| `prepare_dialogue_log_followup.py` | 再生真实单句/相邻/场景日志；保留既有运行别名，治理校订在别名前应用 |
| `prepare_mixed_log_followup.py`、`verify_mixed_log_followup.py` | 通知与对白的有限组合矩阵，不证明无限序列或未知条目均可翻译 |
| `prepare_lead_followup.py`、`prepare_map_ui.py` | 线索运行别名、组合规则及地图白名单；前者 `--runtime-cases` 生成冻结TSV |
| `prepare_biography_followup.py`、`prepare_notification_list_followup.py` | 简介组合及真实个体粗体名单；人物重放只用冻结头像，不造解锁 |
| `audit_irma_dialogue.py`、`audit_dialect_dialogue.py` | 从真实TextAsset筛查口语；非标准拼写仅为选择线索，不自动判错 |
| `prepare_ghost_context_followup.py` | 再生幽灵短答、暴行语境及“更大的游戏”回归 |
| `prepare_bernardo_friend_followup.py` | 再生贝尔纳多友谊回应、真实相邻语境及日志组合回归 |
| `prepare_othello_vizier_followup.py` | 再生高级大臣一词及实际相邻语境回归 |
| `tools/patch/prepare-font-characters.py`、`build-shareable-font.py` | 再生受控字体字符集，装配真实Unity2018生成的图集；源字体与旧模板均不入Git |
| `prepare_othello_log_cache_followup.py` | 从真实冻结日志和边界再生88项缓存/控件复用输入；新探针输入为 `ELSINOREHAN_PROBE_STRICT_LOG_CASES` |
| `tools/translation/verify-recursive-ui.ps1` | 真实XUnity递归消费者组件检查，不启动游戏 |
| `tools/patch/run-toggle-probe.ps1` | 后台游戏探针；具体环境变量和断言契约见源码与对应任务文档 |

上表未写目录的Python脚本均位于 `tools/translation/`。全量重复夹具及中间审计结果按现有 `.gitignore` 保留本机；来源摘要、生成器、代表性回归和核验记录纳入Git。

## 阶段与历史证据

| 阶段 | 记录入口 |
| --- | --- |
| 全文生成及早期样板、界面审计 | [全文记录](sol-full.md)、[界面审计](ui-audit.md)、[历史研究索引](README.md) |
| 日志/UI/字体及阅读页面演进 | 上述接手入口中的对应任务文档；具体数量、运行编号与边界见[迁移快照](handoff-history-2026-10-11.md) |
| 2026-10-10正式1.5.0安装 | [阅读跟进](reading-followup-2026-10-10.md)、[安装证据](../../../runtime/evidence/reading-install-verification.json) |
| 2026-10-11正式1.5.1安装 | [游玩跟进](playthrough-followup-2026-10-11.md)、[安装证据](../../../runtime/evidence/playthrough-install-verification-2026-10-11.json) |
| 2026-10-11待安装对白校订 | [更大的游戏](larger-game-followup-2026-10-11.md)、[友谊回应](bernardo-friend-followup-2026-10-11.md)、[最新候选证据](../../../runtime/evidence/bernardo-friend-followup-verification.json) |
| 2026-10-11正式1.5.2字体与对白安装 | [字体构建与验证](font-replacement-2026-10-11.md)、[候选快照](../../../runtime/evidence/font-replacement-verification.json)、[安装证据](../../../runtime/evidence/font-replacement-install-verification.json)；前述待安装对白已随本轮安装 |
| 2026-10-12正式1.5.3日志缓存安装 | [日志跟进](othello-log-followup-2026-10-12.md)、[安装核验](../../../runtime/evidence/offline-log-cache-install-verification-2026-10-12.json)；字号和字库保持用户选定的当前大小 |

百炼四模型比较已停止，不恢复调用；密钥只在被忽略的本机文件中。PipistrelloHan的IL2CPP/BepInEx6/CSV方案不能直接套用于本项目。旧测试与存档事故的限制保留在原记录中，后续通过不能追认此前存档未变或全剧情已验收。
