# 汉化维护交接

更新时间：2026-10-18。本文维护当前状态、实现注意事项和记录入口；长期执行约束见 [AGENTS.md](../../../AGENTS.md)，仓库介绍和使用方法见 [README.md](../../../README.md)。每次修改在对应任务文档记录详情，完成安装后再更新本页的正式安装状态。

## 当前状态

| 项目 | 状态与依据 |
| --- | --- |
| 维护阶段 | 中文初稿已可玩，继续根据实际游玩反馈定向校订，不等待全分支人工审校 |
| 已安装日志规则 | 已随1.5.7安装157动态规则；补齐真实日志尾段结束缩进/换行封套，45,543资源用例及隔离缓存/F8与真实保存日志通过，见[漏译核查](ambient-log-followup-2026-10-15.md)与[候选证明](../../../runtime/evidence/ambient-log-verification-2026-10-15.json) |
| 已安装书页修复 | 1.5.9已安装：包含1.5.8内存去字/原生层级修复，并补上GameOverUI单页确认入口；11页/F8/悬停回归及13组确认页标题重放通过。见[书页视觉修复](ending-book-paper-followup-2026-10-17.md)、[确认页修复](ending-confirmation-followup-2026-10-17.md)与[候选证明](../../../runtime/evidence/ending-confirmation-verification-2026-10-17.json) |
| 正式安装 | 插件1.5.9，17,068词条，157动态规则；[最新安装核验](../../../runtime/evidence/legacy-term-install-verification-2026-10-18.json)；包含求婚答复串译修复、LEGACY“基业”校订及此前全部修复，未启动用户游戏 |
| 待安装时间线盘问 | 首次question按用户确认改为“贝尔纳多开始盘问布莉特。”，后两次interrogate保留“审问”；3项真实消费者、16项治理测试通过。用户游戏运行中，候选未安装，见[校订记录](brit-question-followup-2026-10-18.md)及[候选核验](../../../runtime/evidence/brit-question-verification-2026-10-18.json) |
| 待安装离开前安排对白 | 波洛涅斯改为“临走前总该做些安排——不过，我已不欠宫廷什么了，再由我来操办，也没什么意义。”；4项真实正文/对话框封套/日志消费者、16项治理测试通过，见[校订记录](polonius-preparations-followup-2026-10-18.md)及[最新候选核验](../../../runtime/evidence/polonius-preparations-verification-2026-10-18.json)。用户游戏运行中，未安装 |
| 已安装求婚答复 | `I will.`对话框串译为“我会动手。”已通过精确行高封套别名修复；6项真实片段缓存回归、4项正文/日志消费者及16项治理测试通过。见[修复记录](proposal-reply-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/proposal-reply-verification-2026-10-18.json)；已随标题校订合并安装 |
| 已安装结局标题 | 按用户确认将LEGACY“传承”改为“基业”，26项真实标题消费者通过，字体与插件不变；见[用词与安装记录](legacy-term-followup-2026-10-18.md) |
| 待安装结局用词 | 用户要求全部标题词为二字：地位、凡躯、厮守、众人、享乐已应用候选，其余保留；并修正王后称谓、体重搭配和用户选定的“可是，妈的，他就是愿意试一试。”。26项标题及9项正文消费者、18项治理测试通过；新增“厮”已核查现有字体含字，见[最终用词与范围](ending-terms-followup-2026-10-18.md)及[最新候选核验](../../../runtime/evidence/ending-terms-verification-2026-10-18.json)，尚未安装 |
| 待安装葬礼姓名对白 | 两人的正式称呼维持“某某女士”，自称引文保留“吉尔——”的中断；按用户确认显化“吉尔登斯吞是我的姓，那我的名到底是什么？”，后句改为“我连个名都没有！”，开头用“刻着我名字”承接“姓和名都要”，保留原配角自嘲及斜体。7项真实消费者及18项治理测试通过，见[校订记录](guilda-name-followup-2026-10-18.md)及[最新候选核验](../../../runtime/evidence/guilda-monument-verification-2026-10-18.json)，尚未安装 |
| 待安装墓地死亡话题 | 按用户确认将女主的“嗯。真阴郁。”改为“嗯，你这想法可够瘆人的。”，哈姆雷特保留“务实”；4项真实消费者及18项治理测试通过，见[校订记录](graveyard-morbid-followup-2026-10-18.md)及[最新候选核验](../../../runtime/evidence/graveyard-morbid-verification-2026-10-18.json)，尚未安装 |
| 待安装聚会对白 | morbid按确认改为“晦气”；奎因斯改为“啊，亲爱的马塞勒斯，多谢你想到我。”及“身为舞台的掌控者，我的位置在幕后——无人看见，无人想起。”。11项真实消费者及18项治理测试通过，见[校订记录](party-dialogue-followup-2026-10-18.md)及[最新候选核验](../../../runtime/evidence/party-dialogue-verification-2026-10-18.json)，尚未安装 |
| 最新对白校订 | 幽灵“一场更大的游戏”、贝尔纳多“至少，我还有你这个朋友”、奥赛罗“苏丹麾下的一名高级大臣”均已安装；“抓住你的脑袋”按用户决定保留，见[奥赛罗术语核查](othello-term-review-2026-10-11.md) |
| 本轮对白校订 | 奥赛罗故事“我感觉她把我留在了那里好多年”“说来有些病态，我也想让她吞食我的心”、奥菲莉娅“你……你和她……有过肌肤之亲吗？”均已安装，见[本轮记录](othello-story-followup-2026-10-15.md)与[安装核验](../../../runtime/evidence/othello-story-install-verification-2026-10-15.json) |
| 已安装寝宫对白 | 哈姆雷特“你这杀人害命、背信弃义的女人！”已安装，6项真实消费者及15项治理测试通过；国王“在楼下睡着”有原文downstairs及寝宫楼梯顶端标记支持，原译保留。见[核查与范围](royal-chambers-followup-2026-10-17.md)及[候选证明](../../../runtime/evidence/royal-chambers-verification-2026-10-17.json)；插件保持1.5.9 |
| 已安装调情与订婚对白 | “你这姑娘，胆子可真不小。”及“和——奥菲莉娅？”均已安装，后者保留原斜体；6项真实消费者及15项导出治理测试通过。见[调情校订](claudius-cheeky-followup-2026-10-17.md)、[订婚介词修正](brit-betrothal-followup-2026-10-17.md)及[安装核验](../../../runtime/evidence/brit-betrothal-install-verification-2026-10-17.json) |
| 已安装母子感情校订 | 按用户确认将“你让我与儿子分离”改为“你毁了我们母子的感情”，保留后半句失去父亲及原斜体；3项真实消费者、15项导出治理测试通过，已通过安装器更新。见[语境与校订](gertrude-family-followup-2026-10-17.md)及[安装核验](../../../runtime/evidence/gertrude-family-install-verification-2026-10-17.json) |
| 已安装时间线校订 | 鲁特琴第三次搜寻改为“贝尔纳多和哈姆雷特此前没有收获的搜寻仍在继续。”，保留fruitless，不断言整场失败；见[分支核查与校订](lute-timeline-followup-2026-10-15.md)，已随1.5.5安装 |
| 已安装独白校订 | 参考朱生豪、卞之琳的译法润色游戏改写，保留“生存，还是毁灭……”，修正“这是一个值得考虑的问题”及死、睡、梦的断句与节奏；见[独白核查与整段译文](hamlet-soliloquy-followup-2026-10-15.md)，已随1.5.5安装 |
| 已安装人物对白 | 雷欧提斯“憎恨这门新语言”、船上争论的比较与权力差距、格蕾丝以奥马利自称及“恶毒的臭婊子”；详见[对白校订](hamlet-social-dialogue-followup-2026-10-15.md)，已随1.5.5安装 |
| 已安装海盗观察 | 外貌描述“不好惹”改为“粗犷”，保留不修边幅及大海女主人的比喻；未补写容貌损伤。详见[语境与单条校订](pirate-appearance-followup-2026-10-15.md)，已随1.5.5安装 |
| 已安装打斗对白 | 教匕首的annoying/dangerous改为“给对手添点麻烦，还谈不上让你成为多大的威胁”；人命一句按用户建议改为“闹出没必要的人命”。5项真实消费者通过，见[格蕾丝对白校订](grace-combat-dialogue-followup-2026-10-15.md)，已随1.5.5安装 |
| 已安装拇指双关 | 按用户确认，以“他闲着没事，把拇指往屁股里塞，留一根也够用了吧”显化俚语义，保留“一根”斜体；3项真实消费者通过，见[译文与语境](grace-combat-dialogue-followup-2026-10-15.md#拇指玩笑核查)，已随1.5.5安装 |
| 已安装F8修复 | 插件1.5.5：日志已到底部时中英文切换继续保留底部，手动滚离后沿用段落定位；真实隔离UI集成探针对照通过，见[问题与验证](f8-log-bottom-followup-2026-10-15.md)及[安装核验](../../../runtime/evidence/grace-thumb-install-verification-2026-10-15.json) |
| 已安装阅读修复 | 插件1.5.6：日志长姓名后正文自动让位，保留姓名/字号与原文字符串；18人物介绍支持F8同段落与底部保持，108次双向切换通过。另将共享Yes, my lord改为“是，大人。”，保留原文明写Your Majesty的“陛下”。见[本轮修复与边界](reading-layout-followup-2026-10-15.md)及[安装核验](../../../runtime/evidence/reading-layout-install-verification-2026-10-15.json) |
| 本机构建包 | `runtime/package/ElsinoreHan-Sol.zip` 当前为包含聚会三句、墓地死亡话题及葬礼自报姓名校订的1.5.9待安装候选，保留二字结局标题及三条正文、首次盘问、波洛涅斯离开前安排对白及此前全部修复，40文件与ZIP逐项一致；字体、插件、动态规则与许可不变；仍仅为本机个人构建 |
| 备份策略 | 按用户2026-10-15要求停止长期备份；20份旧补丁备份与55份测试存档副本已明确授权删除，释放417,372,433字节。旧安装证据中的备份路径仅为历史记录，已不可用；测试临时存档仍隔离，结束后清理，见[公开上传与清理记录](public-repository-2026-10-15.md) |
| 安装保护证据 | 本次原游戏四文件及8个存档的哈希、修改时间、大小和数量未变；正文词表更新，游戏配置仅移除UTF-8 BOM且解码文本逐字一致，动态词表、插件、字体和许可字节不变，未启动主游戏、未创建备份 |
| 发布状态 | [GitHub源码与译文仓库](https://github.com/Chains-Z/ElsinoreHan)已公开，当前文件与完整历史通过凭证及字体/二进制检查；字体、依赖、游戏、存档和ZIP未上传。可安装补丁包仍仅为本机个人构建，其他依赖许可、完整卸载说明与干净目录安装验证仍待完成，见[公开核验](../../../runtime/evidence/public-repository-verification-2026-10-15.json) |
| 当前字体 | `ElsinoreHan Sans SDF`，来自思源黑体SC Regular 2.005R，OFL1.1；7,660字形及实际运行纹理与原生生成结果一致，“沉”上横检查通过；[字体替换及验证](font-replacement-2026-10-11.md)、[授权争议复核](font-license-risk-check-2026-10-11.md) |

下一步继续处理用户反馈。安装候选时先确认用户游戏已退出，使用安装器核验安装（不创建旧补丁备份），再生成不带 `-PendingInstall` 的包并记录新证据；不要重跑未改变的重型页面验收。公开仓库不上传API Key、字体、依赖、游戏本体、存档和安装包，后续推送可用 `tools/audit_public_repository.py` 扫描当前文件和完整历史。

## 接手入口

| 任务 | 首选资料 |
| --- | --- |
| 最新游玩校订、通知/分享/信息正文修复 | [1.5.1跟进](playthrough-followup-2026-10-11.md)、[更大的游戏](larger-game-followup-2026-10-11.md) |
| 奥赛罗仙境故事与迟疑问句 | [三句校订及安装结果](othello-story-followup-2026-10-15.md) |
| 鲁特琴搜寻简介与真实分支 | [fruitless校订及待安装状态](lute-timeline-followup-2026-10-15.md) |
| 哈姆雷特独白与原著对应 | [开头核查与死亡如睡眠的断句校订](hamlet-soliloquy-followup-2026-10-15.md) |
| 憎恨比喻、船上争论与格蕾丝自称 | [指代、权力差距及粗口力度校订](hamlet-social-dialogue-followup-2026-10-15.md) |
| 船上海盗的外貌观察 | [粗犷与不好惹的语境区分](pirate-appearance-followup-2026-10-15.md) |
| 教匕首、人命语序与拇指玩笑 | [格蕾丝打斗对白及习语解释](grace-combat-dialogue-followup-2026-10-15.md) |
| F8在日志底部向上跳 | [底部定位、手动滚离及真实对照](f8-log-bottom-followup-2026-10-15.md) |
| 日志姓名重叠、人物介绍F8及密会敬称 | [1.5.6排版与人物阅读位置修复](reading-layout-followup-2026-10-15.md) |
| 通知名单、人物简介组合、文档F8 | [阅读界面跟进](reading-followup-2026-10-10.md) |
| 文章与人物口语审校 | [阅读正文](reading-text-review-2026-10-10.md)、[伊尔玛](irma-dialogue-review-2026-10-10.md)、[其他角色](dialect-dialogue-review-2026-10-10.md) |
| 日志组合与滚动位置 | [混合日志](mixed-log-followup-2026-10-10.md)、[日志跟进](log-followup-2026-10-10.md) |
| 最新日志缓存修复、字号核查 | [奥赛罗日志](othello-log-followup-2026-10-12.md)、[候选证明](../../../runtime/evidence/offline-log-cache-verification-2026-10-12.json) |
| 日志尾段、命运书页标题 | [旁听漏译与入侵时间](ambient-log-followup-2026-10-15.md)、[书页四行及图片印字](ending-book-followup-2026-10-16.md) |
| 书页纸块、英文残留及卷页层级 | [完整Sprite坐标、内存去字、11页悬停与软件预览](ending-book-paper-followup-2026-10-17.md) |
| 重温结局后的单页确认标题 | [GameOverUI入口、单页去字、13组标题及1.5.9安装](ending-confirmation-followup-2026-10-17.md) |
| 寝宫斥骂、国王在楼下入睡 | [并列形容词校订与楼梯顶端舞台核查](royal-chambers-followup-2026-10-17.md) |
| 任务按钮F8背景、原英文字号 | [背景修复与原资源核查](lead-background-followup-2026-10-12.md)、[候选证明](../../../runtime/evidence/lead-background-verification-2026-10-12.json) |
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
- 西蒙娜回酒馆的线索原文明写Sunday afternoon，虽然真实脚本允许周日08:01起调度，用户2026-10-16明确决定保留“星期天下午”的原译，不修正原游戏时间提示。
- 13首片尾歌曲、真实工作人员姓名、技术品牌和按键名按实际语境保留。英文强调用途不代表统一强弱等级，依据见 [标记审计](english-markup-audit.md)。

## 实现注意事项

### TMP、缓存与F8

TMP1.4.0的 `SetText` 只写解析缓冲区，getter读取旧 `m_text`。插件在StringBuilder和字符串双参数入口转交原文到text setter；即时路径不拆分，setter前缀通过纯离线API消费，并登记完整组合内存缓存（`Full/scope=-1/persist=false`）。只查 `TryTranslate` 不能保证组合已缓存。源码为 `tools/patch/TranslationToggle.cs`。

1.5.3对 `LogCanvas` 单独从文件词表和真实首匹配Splitter完整重建，再准确覆盖此源内存项；不信任主API可能返回的部分译文或既有混合Full缓存。Alt+R失效重载；未知源重建返回null，上游仍可处理，不能宣称整个管线拒绝未知混合。其他页面保留原路径。当前空替换表、数字模板关闭的配置已验证，不泛化任意可选XUnity配置。

人物Title使用单行自适应字号。`LogScrollAnchor` 只保护F8，不能锁住平时滚动；1.5.5对距日志底部不超过1个UI单位的切换保持末尾，其余位置沿用段落锚点，每次F8重新捕获，手动上滚后不吸回底部。长段内部并非逐词定位，结构或历史变化时保守跳过。当前思源字体合成斜体剪切设为5；旧Arial兼容分支仍为10。参数不是角度，新字体沿用10会导致样本网格相邻边界重叠。TMP1.4迁移旧序列化字段时不能恢复原生SDF8，插件在新字体读取后精确设回SDF8。

1.5.6将阅读保护扩展到真实 `JournalCharactersTab.DescriptionText`，绑定builder、正文和HighlightedPortrait，采用非空段落映射及底部判定；切换头像或正文变化时拒绝旧恢复。模态文档优先。短介绍滚动空间不足时合法边界会限制定位，不把边界夹定报告成零误差。`LogSpeakerLayout` 只在LogCanvas精确indent=16%标签解析后保护正文缩进，按实际姓名末端留间距，不改字符串、缓存、姓名或字号；同时检查中英文及恢复。

1.5.4的 `LeadSplotchLayout` 仅同步真实任务按钮的自动墨迹背景几何，不重跑原Setup或增加颜色监听，不调整字号。原任务预制体与实际中英文任务字号均36，自动字号关闭；Canvas按屏幕高度缩放。布局变化后同步可能延后一帧，回归须等待布局稳定，不能用立即采样冒称当帧像素验证。

1.5.7的书页纸块方案已被用户截图证实有缺陷，勿恢复。1.5.8候选的 `EndingBookLabels` 只读哈希绑定的DXT5书页，在内存中清除英文笔画，新增48号斜体TMP与60号粗体关键词共享原生正文父级，服从卷页遮挡；F8恢复真实原Sprite。坐标必须依据Sprite完整2048×1400矩形及真实关键词列中心，不能拿2041×1322裁剪图直接归一化。关键词仍使用SacrificeWhat/For真实字段，不能误当内部标识排除；字符网格、像素掩码、悬停层级与软件合成预览须分别核验，后者不冒充GPU截图。

1.5.9已安装上述视觉修复，并对 `GameOverUI.Activate` 的916×1252单页 `UI_Book_Unlock` 单独绑定来源及坐标；字段为EndingUnlockTexture、EndingUnlockPage和EndingTitleWhat/For，连接词按原生64号关键词取0.8倍字号。不能以EndingSelectUI的11页通过代替确认页验收。新增探针走真实ActivateGameOver入口，13组标题是控件资源重放，不解锁其它结局或选择命运；EndingId.ToString带类型包装，验证ID须按同类型值比较。

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
| `prepare_othello_story_followup.py` | 再生仙境时间感受、奥菲莉娅迟疑问句、渴望评价及真实相邻日志回归 |
| `prepare_hamlet_soliloquy_followup.py` | 再生完整独白、憎恨比喻、船上争论与船长自称的裸句、角色及真实相邻日志回归 |
| `prepare_pirate_appearance_followup.py` | 再生海盗外貌裸句、角色日志及强盗原译保留回归 |
| `prepare_grace_sword_followup.py` | 再生格蕾丝打斗语境及人命语序的5项真实消费者回归 |
| `prepare_grace_thumb_followup.py` | 再生格蕾丝拇指双关裸句、角色日志及真实相邻语境的3项消费者回归 |
| `prepare_log_speaker_followup.py` | 再生my lord指令/短答、Your Majesty保留及长姓名日志的9项真实消费者，另生真实资源TMP重放输入 |
| `tools/patch/verify-reading-layout.py` | 绑定日志预制体姓名/正文几何与全部实际头像介绍的F8来源、控件、段落、底部及手动滚动，不冒充逐词/像素验收 |
| `tools/patch/verify-log-bottom-anchor.py` | 绑定真实历史和中英文全文，核验日志末尾双向F8及手动滚离；不能用段落restored替代底部断言 |
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
