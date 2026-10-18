# 汉化维护交接

更新时间：2026-10-19。本文维护当前状态、实现注意事项和记录入口；长期执行约束见 [AGENTS.md](../../../AGENTS.md)，仓库介绍和使用方法见 [README.md](../../../README.md)。每次修改在对应任务文档记录详情，完成安装后再更新本页的正式安装状态。

## 当前状态

2026-10-19项目完成公开发布并进入按反馈维护阶段；用户准备卸载游戏并删除全部本地项目，以GitHub仓库与Release为后续唯一项目来源。已保存原插件构建指纹、7661字形字体装配证明及其原生字形元数据，新增离线维护环境恢复工具；AGENTS移除过时的模型比较提醒，明确围绕完成的GPT-6.1-sol译文及现有校订维护。真实从公开仓库干净克隆、再次下载v1.0.0附件，恢复39运行文件及依赖后重新导出、重打包，69文件逐项与云端一致；448份冻结批次原件未变，19项导出与15项发布／恢复局部测试通过。原始运行包、v1.0.0标签、玩家安装及存档未改；个人检查点不上传，GitHub不能恢复玩家进度。Steam指南已由用户公开：[下载与反馈指南](https://steamcommunity.com/sharedfiles/filedetails/?id=3822643409)。见[最终交接与新环境恢复](../../archive/project-handoff-2026-10-19/README.md)及[恢复核验](../../../runtime/evidence/project-handoff-verification-2026-10-19.json)。

2026-10-19按用户要求原样保留汉化声明首句（含保留一切解释权利），后文限定依法享有的译文／校订权利并保留LGPL与第三方许可例外；仓库、包内及发布说明同步。新增带网盘占位的Steam指南草稿，未代发Steam、未放入玩家包。核对Valve官方报告：原版Steam Deck为Verified，Windows／macOS／Linux原生版均存在；本汉化未实机验证，明确要求SteamOS以Proton运行Windows版并配置winhttp覆盖，不能直接用于原生Linux版。1.0.0 Release已更新且为Latest，69文件逐项回读一致，39运行文件不变，11项局部检查通过；完整仓库155提交／1392文件／2605历史blob扫描无已识别风险，ZIP SHA256为8cc8121aac0b4726d8568b68b6b496a2fa1418dbb8d3da203227ee1a059f166e。未启动游戏或改动玩家安装／存档。见[声明与指南](../public-release/localization-statement.md)、[Steam Deck核查](../public-release/steamdeck.md)、[专题核验](../../../runtime/evidence/public-release-localization-statement-verification-2026-10-19.json)及[当前发布核验](../../../runtime/evidence/public-release-1.0.0-published-2026-10-19.json)。

2026-10-19按用户选择为原创插件、工具脚本与配套技术文档采用LGPL-2.1-or-later；根LICENSE为标准完整文本，LICENSE-SCOPE.md明确版权、范围及或更高版本。GitHub已识别为LGPL-2.1；用户可选择后续版本，LGPL不禁止收费或强制提交回本仓库，协作通过Issue／PR倡议。游戏原文、译文、剧情数据及第三方内容不归该代码许可统一授权。[1.0.0发布包](https://github.com/Chains-Z/ElsinoreHan/releases/tag/v1.0.0)已补齐项目许可2份与17文件插件源码归档：69外层文件、18份许可、39运行文件完全不变；13个实际编译源文件逐项匹配产生已安装DLL的原构建记录。11项局部检查及原安装器清单核验通过，全部云端附件回读一致，ZIP SHA256为4dedf2e9eb4852cfbdd449aee6262b72a4beba87d56ea845bf656810e3d8b6f6。根README、包内说明、发布页和AGENTS已同步。未启动游戏、未改玩家安装或存档，检查点保持此前恢复状态。见[授权与源码随附](../public-release/project-license.md)、[专题核验](../../../runtime/evidence/public-release-project-license-verification-2026-10-19.json)及[当前发布核验](../../../runtime/evidence/public-release-1.0.0-published-2026-10-19.json)。

2026-10-19按用户要求将对外汉化补丁版本独立设为1.0.0，内部兼容插件仍为1.5.15；唯一版本配置为tools/release/version.json。已正式发布[最新Release v1.0.0](https://github.com/Chains-Z/ElsinoreHan/releases/tag/v1.0.0)，旧编号Release及其标签均已按用户要求删除，仅保留v1.0.0，历史提交及证据保留。新包根目录为安装方法／使用说明／常见问题／更新说明四份中文TXT，带BOM的UTF-8、记事本可读；补充长按Ctrl约1秒跳过演职人员名单，并明确支持64位Windows。39运行文件与旧包逐字节相同，66文件白名单及8项局部测试通过，安装器可核验新清单；云端全部附件回读一致，ZIP SHA256为a62fe4dbbc60ad8293792d89d48ba1cfd1537f3d26c59cc407085e91e98c0288。仓库README、包内说明及发布页署名：翻译GPT-6.1-sol，校对GPT-6.1-sol与Chains-Z；范围采用用户最终确认的“已经人工游玩所有路线，应该没有重大翻译错误，但不代表已穷尽所有已知对白，也不保证每句对白都经过逐句校对”。项目AGENTS已补版本、公开包及署名约定。本轮未启动游戏或改动玩家安装／存档，沿用此前检查点恢复状态。见[发布核验](../../../runtime/evidence/public-release-1.0.0-published-2026-10-19.json)、[版本约定](../public-release/versioning.md)及[公开包任务](../public-release/README.md)。

历史发布记录（旧编号Release及标签均已删除）：2026-10-19曾公开[原始发布提交 e460b97](https://github.com/Chains-Z/ElsinoreHan/commit/e460b97e238dcfdb794fee068018dccf9ad5a8f6)：平铺ZIP 66文件／39运行文件，16许可及完整Doorstop对应源码；云端ZIP与校验文件逐字节回读一致，SHA256为3c702b733c4bbcb0e9736492801fd0d1aca377b8393b961854e6cc1ac576f092。发布标签对应e460b97源码。完整历史144提交／2,509 blob及当前1,376文件未发现已识别凭证、存档或字体／游戏二进制；备份和测试内容不入包／Git。主游戏15条全部安装，无待安装；主存档已恢复第58轮检查点，原检查点仅保留本地。见[发布核验](../../../runtime/evidence/public-release-published-2026-10-19.json)及[任务入口](../public-release/README.md)。

2026-10-19按用户明确授权安装累计15条校订，并恢复第58轮特殊结局前检查点：38运行文件一致，原游戏4文件不变，恢复后8存档与原备份内容及mtime一致，保留检查点。公开发布准备完成：66文件平铺ZIP可直接解压，39运行文件、16许可及Doorstop对应源码，72项对白／17,069字典检查沿用通过；18项安装器、4项包边界回归及真实干净副本13项UI断言通过，两种卸载流程与268原始文件核对通过，临时副本已清理。目前无待安装内容，准备按用户要求上传GitHub Release。见[发布工作入口](../public-release/README.md)及[验收边界](../public-release/verification.md)。

2026-10-19按用户确认校订空城独白3句：画像Not really改为真的不可能，祭坛显式写出我在想，母亲坟墓改为恐怕我和你。新增3条准确旧值覆盖，累计15词条待安装；72项真实消费者、17,069项字典解析及40文件ZIP通过，无新增字，插件／字体／动态规则不变。另用原GameDataGenerated核对码头句：此前清单中的完整回应仅为旧资源稿，当前对应分支只有省略号，正文回应清单应为5处。未安装或访问存档。见[完整改前／改后及码头纠正](empty-castle-followup-2026-10-19.md)及[最新候选](../../../runtime/evidence/empty-castle-wording-verification-2026-10-19.json)。

2026-10-19按用户确认将升格后重返埃尔西诺对白care to see改为“我当然也没兴趣见<i>他们</i>中的任何一个。”，保留斜体，体现冷淡意愿。新增1条准确旧值覆盖，累计12词条待安装；63项真实消费者、17,069项字典解析及40文件ZIP通过，无新增字，插件／字体／动态规则不变。未安装或访问存档。见[完整改前／改后](ascension-parallel-nice-2026-10-19.md#后续care-to-see的冷淡意愿)及[最新候选](../../../runtime/evidence/ascension-care-verification-2026-10-19.json)。

2026-10-19按用户确认将升格结局naïve由天真改为幼稚、simple由简单改为单纯，并采用确认过的整句表述。新增2条准确旧值覆盖，累计11词条待安装；60项真实消费者、17,069项字典解析及40文件ZIP通过，无新增字，插件／字体／动态规则不变。未安装或访问存档。见[完整改前／改后](ascension-parallel-nice-2026-10-19.md#后续naïve与simple)及[最新候选](../../../runtime/evidence/ascension-naive-simple-verification-2026-10-19.json)。

2026-10-19按用户配音反馈，将升格结局三种动因放到句末：“我见过无数血腥、非自然的死亡，源于色欲、贪婪……怜悯。”，在末词前停顿，不再后置所致；compassion保留同情苦难的怜悯义。新增1条准确旧值覆盖，累计9词条待安装；54项真实消费者、17,069项字典解析及40文件ZIP通过，无新增字，插件／字体／动态规则不变。未安装或访问存档。见[用词及停顿说明](ascension-parallel-nice-2026-10-19.md#后续怜悯落在配音末尾)及[最新候选](../../../runtime/evidence/ascension-compassion-verification-2026-10-19.json)。

2026-10-19将升格结局a dozen more worlds由十二个世界改为十来个世界，保留约十二的数量规模及游历概述语气，不泛化成无数。新增1条准确旧值覆盖，累计8词条待安装；51项真实消费者、17,069项字典解析及40文件ZIP通过，无新增字，插件／字体／动态规则不变。未安装或访问存档。见[用词说明](ascension-parallel-nice-2026-10-19.md#后续a-dozen的概数)及[最新候选](../../../runtime/evidence/ascension-dozen-verification-2026-10-19.json)。

2026-10-19按用户最终选择将结局nothing改为“我对他们所有的爱与恨都已消失，只剩下……空无一物。”，保留剩下之后的停顿。新增1条准确旧值覆盖，累计7词条待安装；48项真实消费者、17,069项字典解析及40文件ZIP通过，无新增字，插件／字体／动态规则未变。未安装或访问存档。见[完整改前／改后](ascension-parallel-nice-2026-10-19.md#后续nothing的内心空无)及[最新候选](../../../runtime/evidence/ascension-nothing-verification-2026-10-19.json)。

2026-10-19按用户截图校订升格终局2句：以躯壳、物件、人偶、角色四个二字名词保留物化并列，昆斯nice改为见到同类竟会让我这么高兴。新增2条准确旧值覆盖，累计6词条待安装；45项真实消费者、17,069项字典解析及40文件ZIP一致通过，无新增字，插件／字体／动态规则不变。未安装或访问存档。见[两句完整改前／改后](ascension-parallel-nice-2026-10-19.md)和[最新候选](../../../runtime/evidence/ascension-parallel-nice-verification-2026-10-19.json)。另补[父亲触发条件与李尔王引用核查](polonius-despair-review-2026-10-19.md#触发原因及原剧引用补核)，不将现译误称经典译本。

2026-10-19按用户截图审查父亲跳下城墙的完整Witch_PoloniusDespair：父亲8句、女主1句全量核对，保留游戏摘引李尔王的8句，仅将女主末句改为“到最后，他已经神志不清了。”，消除重复。新增1条覆盖，连同此前升格3句累计4词条待安装；39项真实消费者含完整连续日志与镜面双源、17,069项字典解析及40文件ZIP通过，无新增字，插件/字体/规则不变。未安装或访问存档。见[完整中英正文及逐句检查](polonius-despair-review-2026-10-19.md)和[候选核验](../../../runtime/evidence/polonius-despair-verification-2026-10-19.json)。

2026-10-19按用户确认将真实感一句改为“太容易了。我甚至都不觉得他们是真实存在的人了。”，明确they指人物及女主主观感受。新增1条准确旧值覆盖，连同此前钟声／道德判断合计3词条待安装；10项真实消费者、17,069项字典解析和40文件ZIP一致通过，无新增字。插件/字体/动态规则不变，未安装或访问存档。见[用词记录](ascension-reality-wording-2026-10-19.md)及[最新候选](../../../runtime/evidence/ascension-reality-verification-2026-10-19.json)。

2026-10-19将杀人后自省句按两句共同意义重组为“就算他们会在下一个世界回来，这么做也还是不对。”，避免孤立的无关紧要。新增1条准确旧值覆盖，连同此前午夜钟声句合计2词条待安装；7项真实消费者（含连续发言日志）、17,069项字典解析和40文件ZIP通过，无新增字。插件/字体/动态规则不变，未安装或访问存档。见[改前／改后](ascension-morality-wording-2026-10-19.md)及[最新候选](../../../runtime/evidence/ascension-morality-verification-2026-10-19.json)。

2026-10-19已从原IL确认升格目击只比较玩家/NPC的CurrentRoom.Id是否相等，不检查距离、视线、朝向或遮挡；notneeded_react还要求对应13名角色未死。地图也按当前房间分组，但只为TinyPortraitOf非空的人建头像，故少头像不能证明无人，不能用时间线头像表反推房间安全。应在反应执行时确保同房没有其他活着的主要角色。见[路线补充](ascension-route-2026-10-19.md)及[原IL与源场景](../../../runtime/evidence/ascension-witness-source-2026-10-19.json)，只读核查，未启动游戏或访问存档。

2026-10-19核对首次集会后的实际行动：demontripped触发49项专用背景安排，含12人各两阶段站位、巡逻、回退站位、知情后躲藏与调查跟踪。第一次集会设封锁状态；没有全员永久绑定不独处的统一规则，但人物不会照旧执行普通日程，并随计数阈值5/8逐步集中。跟踪还需王后报信等设置调查意愿。原AI按每人的调度目的地行动，背景可被剧情抢占。已补[路线说明](ascension-route-2026-10-19.md)及[资源与原IL证据](../../../runtime/evidence/ascension-behavior-source-2026-10-19.json)；只读核查，未启动游戏或访问存档，不承诺固定无失败顺序。

2026-10-19补正升格路线的警报说明：用户在空码头杀雷欧提斯仍被号角召集，真实SC_WITCH_InitialMeeting仅以demontripped触发，场景直接播放号角并叙述发现尸体，不检查目击或NPC实际发现尸体；集会随后才根据人物知情决定指认分支。独处只能避免该次目击知情，无法避免全局集会，警报本身不等于失败。另有5/8口令计数门槛集会。已更新[路线说明](ascension-route-2026-10-19.md)及[来源证据](../../../runtime/evidence/ascension-alarm-source-2026-10-19.json)，仅只读资源核查，未启动游戏或访问存档。

2026-10-19按用户截图定向修正升格赠送对白：“等星期五午夜的钟声响起，如果你已经对每个人都用过这种力量，我们就再好好谈谈。”保留原文加粗，新增1条准确旧值覆盖；3项真实消费者和17,069项实际字典解析通过，无新增字，40文件ZIP一致。本轮1词条待安装；已安装18条昆斯对白不变，未访问存档。见[用词记录](ascension-midnight-wording-2026-10-19.md)及[最新候选](../../../runtime/evidence/ascension-midnight-verification-2026-10-19.json)。

2026-10-19用户明确要求恢复特殊结局共同检查点，已在游戏退出时完成：从before-special-endings-20261019-040551恢复8文件，原备份清单大小/SHA256通过，恢复后哈希、大小、mtime逐项与备份一致，第58轮MainGame。保留原备份，临时回滚副本已清理，未启动游戏；烧书后的本地进度已撤回，当前补丁不变。见[恢复核验](../../../runtime/evidence/special-ending-checkpoint-restore-2026-10-19.json)及[备份记录](special-ending-backup-2026-10-19.md)。另一终局步骤见[升格路线](ascension-route-2026-10-19.md)：周五07:00起获得全体退场后，先用菜单重启时间回周四（信息持久保留），赶在雷欧提斯10:00离开前处理；同轮周五午夜前达成12人死亡与demontripped，随后自动升格采用。避免同房间存活者知情；未执行真实剧情验收。

2026-10-19已通过安装器安装烧书后昆斯18条校订，含用户最终确认的“可惜，亲爱的，<i>我</i>想。”；插件仍1.5.15，17,069词条、157规则、7,661字形。38运行文件与40文件已安装ZIP一致，原游戏4文件和8个存档的哈希、大小、mtime及数量不变；未启动游戏或恢复存档，无待安装修改。复核全部21处烧书状态及对白引用：昆斯三分支31句之外，晨间还含女主独白与哈姆雷特一句回应，未发现其他角色针对烧书的专属新对话；既有普通对白不在排除范围。见[安装核验](../../../runtime/evidence/post-burn-dialogue-install-verification-2026-10-19.json)。

2026-10-19按用户确认将昆斯答复改为“可惜，亲爱的，<i>我</i>想。”，去掉倒字并保留斜体；相对上一候选仅1条中文变化，累计仍18词条待安装。93项本段真实消费者、17,069项实际字典解析及40文件ZIP一致性复验通过；未安装或操作存档。当前候选指针改为[最新核验](../../../runtime/evidence/post-burn-reply-verification-2026-10-19.json)，下述初版证据保留历史快照。

2026-10-19新增烧书后昆斯对白候选：真实scenes_smalltalk的POSTEND_QuinceBookBurned首次27句、第二次2句、后续重复2句全部审查，校订18句，修正计日衔接、理由指代、独白断句、模糊混同的比喻及敌对关系；共享What?因无法只改此处仍保留什么。129项治理、93项本段及642项受影响阅读消费者通过，17,069项实际XUnity解析、708组变体及33别名通过，无新增字，40文件ZIP一致。插件仍1.5.15；此前已安装状态保持，本轮18词条待安装，未恢复或修改玩家存档。见[逐句改前／改后](post-burn-dialogue-2026-10-19.md)及[候选核验](../../../runtime/evidence/post-burn-dialogue-verification-2026-10-19.json)。另已完成[烧书后选择限制与漏译核查](post-burn-availability-2026-10-19.md)：正常书页入口隐藏选择／重温及烧书按钮，94项可见源及127项真实消费者无漏译；88组状态／176次原IL谓词重放通过，不称真实游戏E2E，未访问存档。

2026-10-19当前候选已通过安装器全部安装：含自动派生、双源／地名与对白校订、恢复戏剧大师及轻蔑语境，共561处词条目标变化；插件仍1.5.15，当前无待安装修改。38运行文件与40文件已安装ZIP一致，原游戏4文件及原8存档的哈希／大小／mtime均未变。只读确认玩家第58轮已完成11普通结局、戏剧大师线索与最后现身，烧书已解锁，两个特殊终局均未完成，尚无NotNeeded。按用户本次明确要求保留一份完整8文件共同检查点，路径及烧书操作见[备份与路线](special-ending-backup-2026-10-19.md)，不得当作临时测试存档自动清理。见[安装及备份核验](../../../runtime/evidence/playmaster-tone-install-verification-2026-10-19.json)。

2026-10-19按用户最终反馈恢复戏剧大师，并复核全部33个Playmaster词条及对白上下文：30个保留称号，王后／贝尔纳多／克劳狄斯三句轻蔑身份的说法改用艺人，另重组波洛涅斯的丑角句法，马塞勒斯激将句仅恢复称谓。三份规范译文自动同步六个变体，其余27条走准确旧值校订；旧戏班班主阶段保留快照。本轮33处目标变化，累计561词条待安装。129项治理、3,414项派生、4,612项阅读组合及17,069条实际XUnity解析通过；全部英文键不变，708组全覆盖、33别名无失配，无新增字，40文件ZIP一致。插件仍1.5.15，未安装、未访问存档。见[逐句说明与全范围审查](playmaster-tone-2026-10-19.md)及[候选核验](../../../runtime/evidence/playmaster-tone-verification-2026-10-19.json)。

2026-10-19完成单一中文来源与自动格式派生：889份规范译文生成1,784个现有英文查找键、895条格式关系，覆盖708组真实对白及196条历史别名合同；707组一致，I do保留语境例外。迁移统一495个旧变体，未改写实际编译对白；另按用户最终决定将33处Playmaster改为戏班班主，宴席提议改为“那我们开始用餐吧？”，surprise改为“会让他们很意外”。相对上一候选528处目标变化，累计588词条待安装。127项治理、3,414项本轮真实XUnity消费者及4,612项阅读组合回归通过，无新增字，40文件候选ZIP一致。插件仍1.5.15，未安装、未访问存档。今后绑定句子只编辑规范译文，旧校订和别名保留历史快照。见[维护与用词说明](variant-generation-2026-10-19/README.md)及[候选核验](../../../runtime/evidence/variant-generation-verification-2026-10-19.json)。

2026-10-19特殊章节反馈继续校订：未完句由“有……”改成“这……不可能。这一定又是个骗局。”；4条命运用词改为“命运转动得太慢”。相对上一候选新增5处变化，累计60词条待安装。112项范围、18项既有、6项王后资料消费者及19+4+7治理通过，708组变体／33别名通过，无新增字符、40文件候选ZIP一致。王后截图旧段落译文完整，通用更新提示与章节重新激活资料有关，未发现漏译。核实九步破折号及幽灵斜体规则；全部历史变体尚未迁移为单一维护源。班主候选被否定，称号未改。见[本轮说明](perfect-day-feedback-2026-10-19.md)及[候选核验](../../../runtime/evidence/perfect-day-feedback-verification-2026-10-19.json)。

2026-10-19新增地名与主线对白跟进候选：Wittenberg全游戏39条统一为朱生豪译名威登堡，其中32条改名；4条命运步调对白和2条惊惧发声同步修正，本轮38条、与前轮重合1条，合计59词条待安装。109项新消费者、84项双源及137项受影响既有消费者、19+4+7项治理通过；708组变体／33别名无新问题，无新增字符，40文件候选ZIP一致。插件仍1.5.15，未安装、未访问存档。Playmaster建议班主，尚未全局改称。见[完整说明与改前／改后](place-dialogue-2026-10-19/README.md)及[候选核验](../../../runtime/evidence/place-dialogue-verification-2026-10-19.json)。

2026-10-19完成同句资源／运行变体审查：15,181组对白配出708组变体，修正21组、22词条（资源5、运行17），并核对33条显式别名；包括用户确认的诡异整句和不知道／有一点我很清楚。84项新消费者、79项受影响既有消费者及19+4+7项治理／回归通过，无新增字符；40文件候选ZIP一致。插件仍1.5.15，词条17,069、规则157、字体7,661；本轮22词条尚未安装，此前7条结局措辞已安装。完整改前／改后及原因见[专项记录](source-variant-review-2026-10-19/README.md)与[候选核验](../../../runtime/evidence/source-variant-verification-2026-10-19.json)。You have no idea的新译法仍在讨论，未混入共享词条。

2026-10-19七条结局措辞已全部安装：女主强调句、伶王、血气方刚、从政的人、提亲、有违礼俗、即将告别的世界。插件仍1.5.15，17,069词条、157规则、字体7,661字形；38运行文件与40文件ZIP一致，原4文件和8存档未变，当前无待安装修改。另只读核对当前存档：11普通结局已采用，戏剧大师收尾尚未开始；已整理先说服幽灵、再新轮说服哈姆雷特、特殊演出及PerfectDay、最后现身和备份节点的[操作说明](playmaster-checkpoint-2026-10-19.md)。见[安装核验](../../../runtime/evidence/ending-seven-install-verification-2026-10-19.json)及[进度证据](../../../runtime/evidence/playmaster-checkpoint-progress-2026-10-19.json)。以下候选记录保留历史阶段。

2026-10-19再新增一条已验证、待安装结局措辞：按用户确认将“我留下的那个世界”改为“我即将告别的那个世界”，消除创造或遗留某物的歧义，后半段不变。407项真实XUnity离线消费者及19+4项治理检查通过，对照稿已同步；40文件候选ZIP一致，无新增字符。该候选阶段与此前六条合计7条，现均已安装；插件1.5.15、字体和157规则不变。见[本轮记录](world-farewell-2026-10-19.md)及[候选核验](../../../runtime/evidence/world-farewell-verification-2026-10-19.json)。

2026-10-19再新增一条已验证、待安装结局措辞：庭园婚礼的scandalous由“有伤风化”改为用户确认的“有违礼俗”，保留旁人非议、避免额外暗示举止不检点。407项真实XUnity离线消费者及19+4项治理检查通过，对照稿已同步；40文件候选ZIP一致，无新增字符。该候选阶段与此前五条合计6条，后续见本页首条记录；插件1.5.15、字体和157规则不变。见[本轮记录](wedding-customs-2026-10-19.md)及[候选核验](../../../runtime/evidence/wedding-customs-verification-2026-10-19.json)。

2026-10-19再新增一条已验证、待安装结局措辞：按用户最终确认，将“到了二月，他向父亲求娶我。”改为“到了二月，他向父亲提亲，希望娶我为妻。”，后续父女对话保留。407项真实XUnity离线消费者及19+4项治理检查通过，对照稿已同步；40文件候选ZIP一致，无新增字符。该候选阶段与此前四条合计5条，后续见本页首条记录；插件1.5.15、字体和157规则不变。见[本轮记录](ferdinand-proposal-2026-10-19.md)及[候选核验](../../../runtime/evidence/ferdinand-proposal-verification-2026-10-19.json)。

2026-10-19再新增两条已验证、待安装结局措辞：Player King采用用户确认的朱生豪译名“伶王”，整段明确哈姆雷特并顺畅解释讽刺；politician按用户确认改为“从政的人”。407项真实XUnity离线消费者及19+4项治理检查通过，对照稿已同步；40文件候选ZIP一致，无新增字符。该候选阶段与此前强调句、血气方刚句合计4条，后续见本页首条记录；插件1.5.15、字体和157规则不变。见[本轮记录](player-king-politician-2026-10-19.md)及[候选核验](../../../runtime/evidence/player-king-politician-verification-2026-10-19.json)。

2026-10-19再新增一条已验证、待安装结局措辞：hot-headed invader按用户确认改为“血气方刚的入侵者”，并顺畅重组两人比较的整句。407项真实XUnity离线消费者及19+4项治理检查通过，对照稿已同步；候选40文件ZIP一致，无新增字符，插件、字体和规则不变。该候选阶段与此前女主强调句合计2条，Player King称号当时尚在讨论；后续见本页首条记录。见[本轮记录](fortinbras-comparison-2026-10-19.md)及[候选核验](../../../runtime/evidence/fortinbras-comparison-verification-2026-10-19.json)。

2026-10-19新增一条已验证、待安装结局措辞：女主旁白“可是，妈的，他就是愿意试一试。”改为“可他还真就愿意试一试。”，按用户确认保留强调、减轻粗口。407项真实XUnity离线消费者及19+4项治理检查通过，中英对照稿已同步；候选40文件ZIP一致，插件1.5.15、字体与157规则不变。该候选阶段仅此一条，后续见本页首条记录；以下安装记录保留对应阶段。见[本轮说明](ending-emphasis-2026-10-19.md)及[候选核验](../../../runtime/evidence/ending-emphasis-verification-2026-10-19.json)。

2026-10-19三条待安装措辞已全部安装：嫌恶声“呃！”、附和“确实让人反胃”及结局“斗个你死我活”。插件仍为1.5.15，17,069词条、157规则、字体7,661字形；38运行文件与40文件ZIP逐项一致，原4文件及8存档未变，无待安装修改。见[安装核验](../../../runtime/evidence/ending-strife-install-verification-2026-10-19.json)。另已只读核对礼拜堂独白：默认周五12:30准备、13:00开头短段，建议12:45前到场，详见[时序说明](hamlet-soliloquy-timing-2026-10-19.md)。

2026-10-19再新增一条已验证、待安装结局措辞：“让他们斗个你死我活吧。我要出去快活了。”，保留“我”的斜体。结局对照稿已同步，407项结局正文和7项嫌恶对白消费者、19+4项治理检查通过；该候选阶段与此前嫌恶对白合计三条，现均已安装；插件／字体／规则不变。见[本轮记录](ending-strife-2026-10-19.md)及[最新候选](../../../runtime/evidence/ending-strife-verification-2026-10-19.json)。

2026-10-19新增两条已验证、待安装措辞：罗茜“就她那态度？呃！”，吉尔妲“嗯。是啊，确实让人反胃。”。7项真实消费者和19项治理检查通过；插件1.5.15、字体及动态规则不变，候选40文件ZIP一致，未操作主游戏或存档。见[本轮记录](eugh-wording-2026-10-19.md)和[候选核验](../../../runtime/evidence/eugh-wording-verification-2026-10-19.json)。该轮候选为两条；后续新增一条享乐结局措辞后合计三条，现均随本轮安装；插件仍为1.5.15。

2026-10-19已安装1.5.15：已定位片尾约630毫秒的主线程停顿，来自约11万字符职员名单的重复富文本解析及已排队的文字稳定任务。仅排除真实名单正文，并在稳定协程恢复前取消该正文旧任务；两种显示模式均不再执行巨型拆分，提示、F8、Ctrl保留。10FPS真实隔离对照、48项组件断言和33项离线检查通过；38运行文件与40文件ZIP一致，原4文件及8存档未变，当前无待安装修改。首次排版及进程退出的其它开销不在此结论内。见[性能定位与修复](credits-performance-2026-10-19.md)及[安装核验](../../../runtime/evidence/credits-performance-install-verification-2026-10-19.json)。

2026-10-19已安装1.5.14：Ctrl圆环改为逐次累计，每次更新最多推进10%，修复读到半圈、长帧后直接跳满退出；真实隔离场景旧版复现、新版44项组件断言／10组圆环通过，33项离线检查及74项归来分支断言通过。幽灵悔恨的最终两条译文一起安装，当前无待安装条目。38运行文件、40文件ZIP逐项一致，原4文件及8存档未变。见[长帧修复及安装](credits-stall-followup-2026-10-19.md)、[幽灵中文重组](ghost-regret-followup-2026-10-19.md)和[最新安装证据](../../../runtime/evidence/credits-stall-install-verification-2026-10-19.json)。该阶段尚未定位底层停顿；后续1.5.15已定位并消除职员名单重复解析。

2026-10-19已安装1.5.13：片尾正文及提示完成布局、跨过首帧后才累计Ctrl长按，修复开场黑屏期间暗中计时。全游戏《命运之书》补齐21条书名号，奥赛罗并列句保留“我的出身／我的用意”。此前1.5.12的第五次归来修复、243条跨剧姓名统一及借款来源修改一并安装，相对上次安装共265条译文变化；该次安装已完成，之后的长帧修复及幽灵两条已随1.5.14安装。40项真实片尾组件断言、29项手势／探针测试、4077项文字消费者及19+4项治理通过；原4文件与8存档未变，38运行文件及40文件ZIP一致。见[本轮说明](credits-startup-followup-2026-10-19.md)和[最新安装证据](../../../runtime/evidence/credits-startup-install-verification-2026-10-19.json)。

此前候选证据保留历史状态：[归来修复](fifth-ending-return-2026-10-18.md)、[姓名及环境典故核查](shakespeare-names-2026-10-18/README.md)、[借款来源](../../../runtime/evidence/ending-borrowing-verification-2026-10-19.json)。均已合入本轮安装。

| 项目 | 状态与依据 |
| --- | --- |
| 维护阶段 | 中文初稿已可玩，继续根据实际游玩反馈定向校订，不等待全分支人工审校 |
| 已安装日志规则 | 已随1.5.7安装157动态规则；补齐真实日志尾段结束缩进/换行封套，45,543资源用例及隔离缓存/F8与真实保存日志通过，见[漏译核查](ambient-log-followup-2026-10-15.md)与[候选证明](../../../runtime/evidence/ambient-log-verification-2026-10-15.json) |
| 已安装书页修复 | 1.5.9已安装：包含1.5.8内存去字/原生层级修复，并补上GameOverUI单页确认入口；11页/F8/悬停回归及13组确认页标题重放通过。见[书页视觉修复](ending-book-paper-followup-2026-10-17.md)、[确认页修复](ending-confirmation-followup-2026-10-17.md)与[候选证明](../../../runtime/evidence/ending-confirmation-verification-2026-10-17.json) |
| 正式安装 | 插件1.5.15，17,069词条、157规则、字体7,661字形；本轮15条已确认校订全部安装，无待安装。见[安装证明](../../../runtime/evidence/ascension-empty-castle-install-verification-2026-10-19.json) |
| 已安装时间线盘问 | 首次question按用户确认改为“贝尔纳多开始盘问布莉特。”，后两次interrogate保留“审问”；3项真实消费者、16项治理测试通过。见[校订记录](brit-question-followup-2026-10-18.md)及[候选核验](../../../runtime/evidence/brit-question-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装离开前安排对白 | 波洛涅斯改为“临走前总该做些安排——不过，我已不欠宫廷什么了，再由我来操办，也没什么意义。”；4项真实正文/对话框封套/日志消费者、16项治理测试通过，见[校订记录](polonius-preparations-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/polonius-preparations-verification-2026-10-18.json)。已随本轮补字安装 |
| 已安装求婚答复 | `I will.`对话框串译为“我会动手。”已通过精确行高封套别名修复；6项真实片段缓存回归、4项正文/日志消费者及16项治理测试通过。见[修复记录](proposal-reply-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/proposal-reply-verification-2026-10-18.json)；已随标题校订合并安装 |
| 已安装结局标题 | 按用户确认将LEGACY“传承”改为“基业”，26项真实标题消费者通过，字体与插件不变；见[用词与安装记录](legacy-term-followup-2026-10-18.md) |
| 已安装结局用词 | 用户要求全部标题词为二字：地位、凡躯、厮守、众人、享乐已应用候选，其余保留；并修正王后称谓、体重搭配和用户选定的“可是，妈的，他就是愿意试一试。”。26项标题及9项正文消费者、18项治理测试通过；新增“厮”已核查现有字体含字，见[最终用词与范围](ending-terms-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/ending-terms-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装葬礼姓名对白 | 两人的正式称呼维持“某某女士”，自称引文保留“吉尔——”的中断；按用户确认显化“吉尔登斯吞是我的姓，那我的名到底是什么？”，后句改为“我连个名都没有！”，开头用“刻着我名字”承接“姓和名都要”，保留原配角自嘲及斜体。7项真实消费者及18项治理测试通过，见[校订记录](guilda-name-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/guilda-monument-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装墓地死亡话题 | 按用户确认将女主的“嗯。真阴郁。”改为“嗯，你这想法可够瘆人的。”，哈姆雷特保留“务实”；4项真实消费者及18项治理测试通过，见[校订记录](graveyard-morbid-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/graveyard-morbid-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装聚会对白 | morbid按确认改为“晦气”；奎因斯改为“啊，亲爱的马塞勒斯，多谢你想到我。”及“身为舞台的掌控者，我的位置在幕后——无人看见，无人想起。”。11项真实消费者及18项治理测试通过，见[校订记录](party-dialogue-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/party-dialogue-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装街头卖艺笑话 | 用户确认以“荒无人道／惨无人道”串词替代humane／inhumane错词，保留纠正字加粗与嘴硬答复；7项真实消费者及18项治理测试通过，见[校订记录](busking-wordplay-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/busking-wordplay-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装浪漫与短叹 | 用户确认romantic改为“浪漫”、完整Oh.改为“噢。”，共用短叹15处上下文均已核查；21项真实消费者及18项治理测试通过，见[校订记录](romantic-oh-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/romantic-oh-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装街头起哄 | 用户确认按语境将衣袖泛化为衣服：“对啊！把她衣服扒下来！”；4项真实消费者及18项治理测试通过，见[校订记录](busking-sleeves-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/busking-sleeves-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装原木与表白语境 | log按用户确认细化为“池塘那头挡路的那截树干”；here we are改为“而、而现在，嗯……我们已经走到这一步了。”；8项真实消费者及18项治理测试通过，见[校订记录](log-confession-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/log-confession-verification-2026-10-18.json)；已随本轮补字安装 |
| 已安装姓名摆件玩笑 | 用户确认点明“这名字听着不像人名，倒像某种摆在墙角的装饰品”，保留假装介绍陈设的调侃；4项真实消费者及18项治理测试通过，见[校订记录](hamlet-name-followup-2026-10-18.md)及[原候选核验](../../../runtime/evidence/hamlet-name-verification-2026-10-18.json)；已随本轮补字安装 |
| 嫌恶声最新措辞 | 用户最终确认“呃！”与“确实让人反胃”，两条已验证并安装；沿用现有字体，见[本轮说明](eugh-wording-2026-10-19.md) |
| 已安装嫌恶声补字 | 两句Eugh按用户确认使用“噁”；原生生成、实际字体加载与字形图集、115项词表消费者、18项治理及6项字体判定器测试通过；已安装，见[本轮记录](eugh-font-followup-2026-10-18.md) |
| 已安装返回方法答复 | 幽灵裸源和实际斜体统一为“当然知道。可你为什么会有这种念头？”，已随1.5.11安装。见[校订记录](ghost-return-followup-2026-10-18.md)及[安装核验](../../../runtime/evidence/credits-skip-install-verification-2026-10-18.json) |
| 已安装烧毁书页 | 1.5.11已安装普通书页与确认页独立烧毁叠层去字；11页/F8/悬停及13组确认标题资源重放通过，实际重建纹理与离线像素结果一致，软件预览已查看。见[修复与运行记录](ending-burnt-paper-followup-2026-10-18.md)及[安装核验](../../../runtime/evidence/credits-skip-install-verification-2026-10-18.json) |
| 已安装谢幕对白 | 哈姆雷特“四万个兄弟的爱加在一起，也抵不过我的爱——”；幽灵两次go统一“前行”，That is all改“我要说的就是这些。”，裸源/实际斜体同步，已随1.5.11安装。见[兄弟对白](hamlet-brothers-followup-2026-10-18.md)、[幽灵发言](ghost-farewell-followup-2026-10-18.md)及[安装核验](../../../runtime/evidence/credits-skip-install-verification-2026-10-18.json) |
| 已安装片尾跳过 | 1.5.14保留首帧就绪保护，并限制每次更新最多推进10%；中途长帧后继续剩余进度，正常刷新约1秒，低帧率或卡顿时延长。旧版50%后直接补满复现，新版44项组件断言、10组圆环／F8通过；受控输入及采样间隔，不称物理键盘、GPU验收或底层卡顿消除。见[长帧修复及安装](credits-stall-followup-2026-10-19.md) |
| 已安装女王独白 | 已对照真实资源核查33段，修正6段，含卡珊德拉诅咒、姑娘与女王身份对照、创伤后的人的完整性及他国效仿的结尾；其余27段保留。33项真实正文消费者及18项治理通过，字体与插件不变。见[完整审查](queen-ending-followup-2026-10-18.md)及[候选核验](../../../runtime/evidence/queen-ending-verification-2026-10-18.json) |
| 已安装完整结局审校 | 13结局399段正文及3处纯省略号已全部复核，本轮新增15段与1条编译源变体修正，连同女王此前6段累计22条词表变化，已随最新阅读反馈合并安装。407项真实消费者与18项治理通过，附可重读全文；见[审查与阅读稿](endings-review-2026-10-18/README.md)及[最新候选](../../../runtime/evidence/all-endings-verification-2026-10-18.json) |
| 已安装阅读反馈 | 阅读反馈阶段新增41条目标变化：赎金双源、分手语气、37条全称统一为布莉吉塔（昵称布莉特）；MYSELF自我候选已按用户决定恢复自己，相对上次安装累计60条，已通过安装器更新。515项姓名/组合、407项正文、26项标题消费者及19项治理、4项覆盖保护通过。见[四项反馈记录](ending-readback-followup-2026-10-18.md)及[本次安装核验](../../../runtime/evidence/ending-readback-install-verification-2026-10-18.json) |
| 已安装love与归来劝诫 | 全文431项love源及三场148段劝诫已审，本轮25条目标校订已通过安装器安装（图示三处母子爱按用户决定保留）；含在乎/敬爱/情分/喜欢/感情深厚、单方不再爱与3条编译源语义修正。642项专项、407项结局、113项既有语境消费者及19+4治理检查通过；插件/字体不变。附[逐条说明和完整对照稿](love-review-2026-10-18/README.md)及[安装核验](../../../runtime/evidence/love-context-install-verification-2026-10-18.json) |
| 已安装谢幕全分支审校 | 11分支与共用开场/收尾449段、418条实际源均已核查，修正14处发言对应15条词条；加上用户确认的婚姻正文两句，本轮17条已通过安装器安装。570项谢幕、642项love/归来、407项正文及79项日志消费者、19+4治理通过；38运行文件与40文件个人ZIP一致，原4文件及8存档未变。见[逐条说明与全文对照](curtain-call-review-2026-10-18/README.md)及[安装核验](../../../runtime/evidence/curtain-call-install-verification-2026-10-18.json) |
| 已安装公媳称谓补改 | 用户最终确认使用公公和儿媳，裸源/实际斜体统一为“奥菲莉娅。但愿我能给你一个慈爱的拥抱，像公公疼爱儿媳那样。”，新增2条已安装。574项谢幕、642项love/归来、6项定向及6项既有夹具、19项治理通过；38运行文件与40文件个人ZIP一致，原4文件及8存档未变。见[说明与对照稿](curtain-call-review-2026-10-18/README.md)及[安装核验](../../../runtime/evidence/inlaw-install-verification-2026-10-18.json) |
| 当前游玩进度核查 | 第32轮普通命运11/11解锁、正式采用0，线索19/20完成（仅戏剧大师未完），两个特殊终局未解锁；只读核查原8存档未变，结局门槛/分支检查点与验收口径见[进度核查](completion-review-2026-10-18.md) |
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
| 本机构建包 | 公开平铺包 `runtime/package/public-release/ElsinoreHan-v1.5.15-zh.20261019-win-x86.zip`，66文件且含完整许可与对应源码，直接解压可用，详见[发布验收](../public-release/verification.md)；旧个人包保留独立用途 |
| 备份策略 | 按用户2026-10-15要求停止长期备份；20份旧补丁备份与55份测试存档副本已明确授权删除，释放417,372,433字节。旧安装证据中的备份路径仅为历史记录，已不可用；测试临时存档仍隔离，结束后清理，见[公开上传与清理记录](public-repository-2026-10-15.md) |
| 安装保护证据 | 本轮安装前后原游戏4文件及8个存档的哈希、修改时间、大小和数量均未变；通过安装器更新且不创建旧补丁备份。隔离运行测试使用临时存档副本并已清理，未启动或操作用户主游戏 |
| 发布状态 | [v1.5.15-zh.20261019](https://github.com/Chains-Z/ElsinoreHan/releases/tag/v1.5.15-zh.20261019)已公开，平铺ZIP可直接解压，云端附件回读一致。Git只含源码／译文／许可及核验摘要，运行二进制仅随白名单Release分发，存档／密钥／游戏不公开 |
| 当前字体 | `ElsinoreHan Sans SDF`，来自思源黑体SC Regular 2.005R，OFL1.1；7,661字形及实际运行图集与原生生成结果一致，新字“噁”与“沉”上横检查通过，见[最新补字验收](eugh-font-followup-2026-10-18.md)、[字体来源](font-replacement-2026-10-11.md)与[授权复核](font-license-risk-check-2026-10-11.md) |

下一步接收玩家反馈并按真实源定向修复。首个公开Release已发布并回读核对，当前15条全部安装，无待安装。用户存档已恢复至第58轮特殊结局前共同检查点；原检查点保留本地，禁止当临时测试副本删除或上传。测试临时游戏与存档已清理，历史失败与通过证据保留。

## 接手入口

| 任务 | 首选资料 |
| --- | --- |
| 片尾主线程停顿来源与消除 | [1.5.15真实CPU定位、中英文对照及安装](credits-performance-2026-10-19.md) |
| Ctrl中途长帧后直接跳满 | [1.5.14修复、离线及真实运行对照](credits-stall-followup-2026-10-19.md) |
| 片尾开场Ctrl进度、书名号与谢幕并列句 | [1.5.13修复及安装](credits-startup-followup-2026-10-19.md) |
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

- 已安装词表将`Birgitta`统一为布莉吉塔，`Brit`昵称保持布莉特；正式与亲昵称呼不合并。`MYSELF`标题按用户最终决定保留自己，撤回自我候选；不译成仅表示保命的独活；见[阅读反馈](ending-readback-followup-2026-10-18.md)。
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
