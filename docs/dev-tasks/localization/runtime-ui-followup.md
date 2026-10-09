# 日志、通知、文档与长人物名的后续修复

## 2026-10-09 恢复后的最终状态：1.3.0 已安装

用户在新会话明确要求继续后，已完成此前暂停的三项修复并安装：提示中原有双引号保留为中文双引号；哈姆雷特简介增加真实破折号转换后的精确源别名；中文回退字体的TMP合成斜体剪切参数由35降为10。粗体、斜体标签和字符推进宽度不变，35与10不是角度。正式词表16,843条，仍为90条动态规则，其中66条限定UI规则。

哈姆雷特别名逐字复用冻结条目 `p00031-4dfce554591f`，不重译正文；导出器现在也强制核对原ID、原文和译文哈希，拒绝篡改别名译文。源证据见 `analysis/ui-audit/hamlet-bio-alias-evidence.json`，别名为 `translation/supplemental/hamlet-bio-alias.json`。

完整缓存检查另外发现两条旧提示被通用斜体封套抢先匹配：`I don't think {0} cares about this information.` 和 `{0} has already seen this information.`。已收窄封套，让含斜体的完整源交回原格式模板，尾换行使用既有受限规则保存。保持真实XUnity逆序首匹配，失败不换规则兜底；新增7个格式、换行、组合及未知参数回归。

### 最终证据与范围

最终运行 `5f5a90f339c74f2ea2a99d2bc5761fc1` 在独立游戏副本和冻结真实存档副本中通过全部检查。摘要为 [tmp-ui-verification.json](../../../runtime/evidence/tmp-ui-verification.json)，完整资料为 [journal-analysis.json](../../../runtime/evidence/headless/5f5a90f339c74f2ea2a99d2bc5761fc1/journal-analysis.json)，字体原始网格为 [italic-geometry.json](../../../runtime/evidence/headless/5f5a90f339c74f2ea2a99d2bc5761fc1/italic-geometry.json)。

- 全部7个日志索引、14份文档、14名人物标题与正文、实际已知信息分享预览及HUD/Journal/Timeline/F8通过；哈姆雷特正文单独核对英文原文和中文恢复。缓存与显示差异为零，分享提交次数为零。
- 21个冻结缓存用例及2,816个中文字符的字体覆盖通过。真实递归消费者56个日志和616个通知通过。
- 两句截图对白各在真实对白/日志字体参数下比较原剪切、修复剪切及正体，共12份单行网格。两句最小字形包络间距由约-3.60、-5.77变为+2.55、+0.88；斜体仍有可见剪切，正体不倾斜，字符推进不变。
- 离线111项回归通过：导出15、人物别名4、菜单判定22、资料判定37、字体判定28、启动前校验5。缺样本、漏字、乱序、伪造边界、空正文、错误菜单入口等均不能冒充通过。
- 正式安装、测试副本、补丁目录与39文件ZIP的插件及两份词表哈希一致。安装备份为 `runtime/backups/full-2f3dcf514b7345d792543c87149528cd`，原游戏四文件和原存档哈希、修改时间、数量均未变，临时探针和appid已清理，测试进程退出。

这是实际组件与字形网格验证。`-nographics` 不计算正常屏幕布局，字体样本故意禁用自身换行和裁切以完整比较相邻字；没有改变正式组件的换行配置。字形包络取自真实mesh/UV与glyph矩形，排除SDF padding，但未采样纹理alpha，不能称屏幕换行、像素截图、物理F8或全剧情E2E通过。本轮没有访问逐档设置页，仍只保留原设置验收作为历史证据。

### 探针修正与维护入口

上轮字体克隆挂在隐藏对白父级，没有Canvas；现只在真实场景的活跃日志父级创建临时样本。Unity的JsonUtility漏掉动态加载探针的嵌套数组，已显式导出完整网格；判定器核对完整冻结中文、强调范围、模式参数及由实际相邻字计算的间距。

游戏的暂停、Journal导航是延迟请求，拒绝后会清队列。启动探针现在先核对真实Boss/GUI初始化、准入和转换状态，再追踪具体请求是否消费，未生效时最多重试5次；采集按菜单实际就绪后的相对时钟安排。文档入口必须传非空关闭回调，否则真实 `OnClosed` 会抛空引用并中断清理。采集还等待真实转换结束，不强开Canvas或伪造获取状态。

后台Rewired会处理物理输入，之前异常栈已证实取消按键查询导致资料自动关闭。临时探针阻断本进程 `PlayerInputManaged` 的按钮/轴状态查询，并禁用自动输入模块；显式EventSystem事件、真实UiToggle、State/Lookup/HistoryText继续使用。`BLOCKED` 是被阻断的查询次数，不能说观测到相同数量的真实按键。Unity直接按键与正式插件F8入口并未全部封堵，此措施不称完整输入系统隔离，也不安装或打包给普通游玩。

复跑资料和字体需要设置 `ELSINOREHAN_PROBE_JOURNAL=1`、`ELSINOREHAN_PROBE_TOGGLE=1`、`ELSINOREHAN_PROBE_ITALIC=1`，使用 `runtime/game-test/settings-options` 副本；保存源使用 `runtime/backups/probe-save-6f413db42b4842f99a322ede96cdd074`。四个输入分别为：

- `ELSINOREHAN_PROBE_TRANSLATIONS=translation/sol-full-2026-10-09/translations.json`
- `ELSINOREHAN_PROBE_CHARACTERS=translation/sol-full-2026-10-09/chinese-characters.txt`
- `ELSINOREHAN_PROBE_CACHE_CASES=translation/sol-full-2026-10-09/runtime-cache-cases.tsv`
- `ELSINOREHAN_PROBE_CLOSEUP_IDS=runtime/build/closeup-ids.txt`

运行前解析为绝对路径，再调用 `tools/patch/run-headless-probe.ps1`。缺输入或非法重试延迟会在构建/启动前拒绝。资料与字体失败运行保留在 `runtime/evidence/headless/`，不得把早期 `COLLECTED`、单独缓存通过或裁切的网格合并成完整成功；最终通过绑定上述单个运行。下一步只按实际游玩反馈修订，不重译全文，不恢复已停止的百炼比较。

以下保留1.2.0阶段的实施和验收记录，数量及运行ID均属历史快照。

2026-10-09。用户游玩反馈显示，上轮修复仍有对话记录英文、通知中英混排、资料正文漏译和长人物名压住称号。本轮保持既有离线框架及原文粗斜体，针对实际消费路径修复。

## 实现与来源

- 日志验证旧口径不足：`67326bd795924f60a2b5aa5d96f6cb1a` 只绑定首个日志组件，API 返回部分中文也曾被误认为翻译成功。该运行不能证明全部历史已中文。现按全部历史索引绑定实际组件，核对完整组合缓存、英文残留、F8 精确原文及恢复；最后真实空组也必须始终为空。
- 真实 XUnity 按逆序只采用首个匹配规则。旧消费者验证器在该规则返回 null 后尝试下一条规则，与真实行为不同；现已修正。结构边界规则优先，冻结对白续行允许实际源中的行尾空格及省略号。
- 通知新增有限语法：真实人名、七种人物意图、嵌套信念、零参知识显示文本、人物名单和分享首句。覆盖实际终端行高封套与换行，不靠全局英文逐词替换。来源及 596 个消费者用例见 `analysis/ui-audit/notification-source-audit.json` 和 `translation/supplemental/notification-ui-tests.json`。
- 三条 Journal 界面译文由“日志”统一为“笔记”。后续修订分层合并，每层保持源唯一，覆盖必须精确匹配 `previous_target`；冻结模型响应不变。
- 《五月节前夜》的原资源源串为 4236 字符，游戏加载后为 4224：`CompilerPasses.doTextReplacement` 按已核实顺序替换破折号，此文实际只有四处 ` -- `→`—`。新增运行源别名 `runtime-closeup-1c8d4a1a61d37350` 精确复用 `p00025-94d1e00aaac9` 完整译文，未修改游戏资源。别名记录含实际报告哈希与编译器契约。
- 插件 1.2.0 仅为 `CharactersTab/Title` 开启单行自适应字号，保留人物全名，让其在原标题空间内显示，不压住独立 Subtitle。没有全局调小对白或将斜体转换为粗体。

## 验证口径

词表现为 16,842 条，动态规则 90 条，其中限定 UI 规则 66 条。真实 XUnity Splitter/ParserResult 验证日志 49/49、通知 596/596 通过；导出回归 14 项、菜单判定回归 12 项通过。通知用例覆盖源格式与组合语法，不声称逐个实际剧情弹窗或全剧情 E2E 通过。

后台报告 `6f413db42b4842f99a322ede96cdd074` 已核对当前隔离存档的全部 7 个历史索引、14 份实际 Closeup 文档以及 14 名已知人物标题（含布莉特）的完整目标与布局。分享目标“有人想要我的命”在该存档中不可选，故整轮仍严格失败；没有伪造获取状态或把这一项标成通过。后续报告应选择实际已获得信息并核对真实预览，同时保留该截图原句的离线消费者用例。

最终运行 `398ee54ccb6e4318a623e94282762212` 全部断言通过，缓存/显示差异为零。分享页选择实际已获知 `HamletActingMad`，由 `Gertrude_FoulMood` 的真实首句进入预览；信息/场景/源哈希、314句白名单、完整预期译文、实际组件和F8均核对，提交次数为零。危险信息两句由通知真实消费者独立覆盖，报告明确不是本次UI所选场景。资料判定回归最终为34项，新增未知预览拒绝与实际信息来源约束。

插件、两份词表已备份安装，备份为 `runtime/backups/full-9f52dd35473f46148a40b28f99adc37f`。39文件个人ZIP已同步，安装、测试副本、补丁目录与ZIP三份核心产物SHA一致；原exe、UnityPlayer、resources.assets、Assembly-CSharp哈希不变。最新 [核验摘要](../../../runtime/evidence/tmp-ui-verification.json) 与 [完整资料报告](../../../runtime/evidence/tmp-journal-analysis.json) 记录结果。原存档、冻结输入均未变，临时探针/appid及测试进程已清理。

资料模式只检查菜单与实际资料页面，明确省略没有访问的设置页断言，不把它记录为设置验收通过。当前保存目录先复制到项目隔离目录；后台静音运行、存档写入拦截、原目录哈希/时间/数量核对、临时入口还原与进程清理继续保留。如果用户游戏同时运行，必须使用既有冻结存档，原目录变化不能用来推断诊断写入；报告单列该对照的局限。

## 排版决策

中文可以采用斜体，不能将“不普遍采用”说成“禁止使用”。游戏原文中斜体还用于幽灵对白、唱词、引文、作品名和舞台说明，粗体也兼用于语气与结构标签；没有统一强弱等级。按用户当前偏好保留 i→i、b→b，详细原句及规范来源见 [原文标记审计](english-markup-audit.md)。

后台检查不验收像素截图、物理键盘注入、世界内搜寻物件或全剧情分支。真实组件验收、安装与 ZIP 同步状态应以最终核验摘要为准，不以 `COLLECTED` 或词表导出成功替代。
