# ElsinoreHan 项目约定与最新交接

更新时间：2026-10-10。当前阶段：**中文初稿、界面补译与TMP正文兼容修复已安装，继续随实际游玩校订**。本文件只保留项目特有约定、当前进展和接手必需信息；历史选型、原始统计与试译详情见任务文档。

最新状态：本轮线索多段、地图确认、时间线空尾段/房间与嵌套信念修复已正式安装，个人ZIP同步。当前1.3.0、16,861条、121条规则；最终运行 `46a0f4e419554b0e825ff42b5570c7fe` 的真实资料组件、6条线索、3个地图确认、3项时间线详情及资源重放/F8通过，1,538个递归消费者通过。见 [本轮修复](docs/dev-tasks/localization/ui-followup-2026-10-10.md)。字体保持前轮 `5f5a90f339c74f2ea2a99d2bc5761fc1` 的参数与网格证据，不把它算成本轮重验。下一步按实际游玩反馈校订，不自动重复重型测试。

语言、沙盒、Windows通用操作、subagent使用、Git提交和通用测试分级沿用用户级AGENTS，本文件不重复维护。

项目目标是先玩中文初稿，再随游玩校订；完整人工审校不作为开玩的前置条件。项目文档和验证记录集中在 docs/dev-tasks/localization/ 与 runtime/evidence/。

## 接手先读

1. README.md：当前安装、快捷键和入口。
   docs/dev-tasks/localization/ui-followup-2026-10-10.md：最新线索、地图、时间线、嵌套信念与探针修正。
   docs/dev-tasks/localization/runtime-ui-followup.md：最新日志、通知、文档、长人物名和排版决策。
   docs/dev-tasks/localization/tmp-compatibility.md：TMP兼容实现及前轮验证局限。
2. docs/dev-tasks/localization/ui-audit.md：最新界面修复、源审计和实际验收。
3. runtime/evidence/ui-followup-verification.json：最新资料组件、正式安装与ZIP核验；tmp-ui-verification.json保留前轮字体网格证据，ui-audit-verification.json和full-patch-verification.json是历史阶段快照。
4. docs/dev-tasks/localization/sol-full.md：冻结全文、来源、实际CLI用量与维护方式。
5. 需要追溯历史时再读 docs/dev-tasks/localization/README.md；原粗提取统计在 analysis/metrics.json，脚本为 analysis/analyze.py。

不要重复引擎识别、从零选模型或以原粗提取清单重新开始全文翻译。

## 现场与已安装补丁

- 项目：D:\MyProjects\ElsinoreHan；游戏：D:\SteamLibrary\steamapps\common\Elsinore。
- 已验证游戏：Windows x86、Mono，Unity 2018.4.20f1，《Elsinore》1.4.1（3678），主要文字组件为TextMeshProUGUI。
- 补丁结构：BepInEx 5 x86 + XUnity.AutoTranslator 5.6.2 + 中文TMP字体 + 本项目F8/TMP兼容插件1.3.0。词表预制离线加载；Endpoint与FallbackEndpoint均为空，不在游玩时调用翻译API。
- 当前正式词表 **16,861条**：原16,228条加界面修复新增613条、一条文档加载变体、一条哈姆雷特资料变体和18个线索运行别名。原始全文由 gpt-6.1-sol 经现有Codex登录完成112批；后续只定向补译与校订，不重跑全文。
- 共121条动态规则：24个数字/F# %s模板，97条限定UI拆分规则。MaxTextParserRecursion=64支持日期、房间、名单和多段组合；配置变更需重启游戏，Alt+R只重载词表。真实XUnity按逆序只取首个匹配规则，失败不得在验证器中换另一条规则兜底。
- TMP1.4.0的SetText只写解析缓冲区、getter读旧m_text；插件拦截StringBuilder和字符串双参数入口，转交原文到text setter。即时路径不执行拆分，setter前缀以纯离线API消费并明确登记完整组合内存缓存（Full/scope=-1/persist=false），让XUnity维护原文/F8。只查询TryTranslate不能保证组合被缓存；不直接把中文写成游戏原始数据。
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
- 按用户偏好保留斜体对应斜体、粗体对应粗体，不全局转换。斜体还用于幽灵声音、唱词、作品名及舞台说明；粗体也用于结构与任务线索，没有统一强弱等级。原句证据见 english-markup-audit.md。
- 人物页Title限定单行自适应字号，保留全名并避免与Subtitle重叠。运行文档别名源与编译器九步破折号替换契约记录在 runtime-closeup-translations.json，原资源和冻结译文不变。
- 哈姆雷特简介别名为 hamlet-bio-alias.json，逐字复用冻结p00031；导出器核对原ID、原文和译文哈希。通知原有双引号保留为中文双引号，不给无引号分支硬加。1.3.0仅把ARIALUNI SDF合成斜体剪切从35降为10，保留i/b和字符推进宽度；这两个参数不是角度。
- 两条完整斜体格式提示须让原数字模板消费；通用斜体封套会抢先剥掉i导致模板不再匹配，现用精确负向前瞻和既有尾换行规则处理。新源勿绕过真实逆序首匹配契约。

## 验证与存档保护

- 最新本轮验收46a0f4e419554b0e825ff42b5570c7fe：6条实际线索、8组资源线索重放，Hamlet/Upper Hallway/The Walls三个真实地图确认，单人/多人空Changes及乔特鲁德寝室三项真实时间线详情、五组事件格式器重放均完整中文且F8往返通过；历史循环和原详情经真实按钮恢复。7日志/14文档/14人物及分享预览仍通过。145项离线回归、13个真实反射签名及5个真实GameClock日期检查通过；地图仅点否、原位置/暂停时钟未变。安装、测试副本、包目录与39文件ZIP一致，原游戏四文件和本轮原存档未变，临时插件/appid清理、入口按落盘原件字节恢复。重放不代表已获得具体剧情，不称全剧情E2E。

- 最新资料验收5f5a90f339c74f2ea2a99d2bc5761fc1：冻结存档全部7个日志索引、14份Closeup文档、14名人物标题与正文、真实已知信息分享预览及HUD/Journal/Timeline/F8通过，哈姆雷特正文单独核对F8。零缓存/显示差异，原存档哈希/时间/数量未变。21个冻结缓存、2,816中文字符覆盖与12份字体单行网格通过；56个日志和616个通知真实递归消费者及111项离线回归通过。原398ee54为1.2.0历史验收；指定危险句仍仅由真实消费者覆盖，不称该剧情E2E通过。
- 字体样本使用真实对白/日志字体参数和冻结译文，隔离样本关闭换行/裁切以比较完整相邻字，绝不改变正式控件布局。网格与glyph矩形包络排除SDF padding，但不采样纹理alpha；不能称屏幕换行或像素验收通过。JsonUtility会漏动态加载探针的嵌套数组，当前显式导出并严格核对12份完整中文/强调/边界证据。
- 旧67326bd验收只绑定首个日志组件，部分中文API也误当通过，不能证明全部历史已译；已用上述加强检查替代。设置回归daf2eee559244049bceded4e50c30ed1逐档13值仍为历史设置证据，本轮资料模式未访问设置页，不报告设置通过。
- 后台组件/缓存验证不等于物理F8按键注入、像素渲染或完整游玩E2E。全剧情分支、图片文字、未知动态兜底及对白/资料像素排版仍可能需要用户反馈；不得宣称所有界面零漏译。
- 游戏测试不得抢前台或发声。现有入口使用隐藏 -batchmode -nographics -nosound、低优先级和10FPS，确认Wwise暂停并监测窗口；出现窗口或超时就终止自己启动的进程，不回退全屏测试，不要求用户手动截图作为前置条件。
- 默认Application.cctor入口可能迟于游戏分辨率应用；测试期间临时在GameInitialization.Awake前加载保护，跳过后台显示质量/分辨率应用，finally按原字节还原Bep配置。此行为仅临时探针使用，不打包到普通游玩插件。
- 暂停/Journal导航是DeferredAction，拒绝后清队列，不会自动重试。探针须等真实初始化、准入与转换状态，并追踪具体请求消费；不能把requestedPause置真就认定生效。文档入口必须传非空onDone，真实OnClosed无条件调用；等待真实转换结束再采集。
- Rewired后台输入可导致资料自动关闭。临时探针阻断PlayerInputManaged按钮/轴状态查询并禁用自动输入模块，显式EventSystem/UiToggle与真实资料来源不变；BLOCKED是查询阻断次数，不能称真实按键数量。Unity直接按键与正式插件F8并未全封堵，不称完整物理输入隔离或物理键盘E2E，保护不打包给用户。
- 用户在玩时使用 runtime/game-test/settings-options 独立游戏副本，按可执行文件路径区分进程；不关闭或操作用户原游戏。安装脚本要求目标游戏关闭，不绕过保护覆盖运行中的插件。
- 测试先复制真实存档到 runtime/backups/probe-save-*；RuntimeProbe在业务初始化前重定向SaveLoad.SaveFileDirectory，拦截SaveData与旧版迁移。保护建立失败直接终止，避免普通退出再次保存。前后核对原存档文件哈希、修改时间和数量。
- 设置逐档测试只改克隆配置并点取消，不点击确认或应用。真实暂停动作进入菜单，不能仅强行激活Canvas后误报导航成功。
- 临时RuntimeProbe不打包给用户，finally清理插件/appid并确认测试进程退出。实际存档路径为 %APPDATA%\Golden Glitch Studios\Elsinore。
- 修复前一次诊断曾自动加载旧进度并在退出时写回game.save，旧备份未保留，进度差异未知，已告知用户。记录见 docs/dev-tasks/localization/save-write-incident.md；后续隔离通过不代表此前存档未变。

## 维护入口与下一步

- tools/translation/prepare_ui_supplement.py：从审计与既有译文生成补译/规则；只在要更新这组来源时运行，避免覆盖未整理的人工修订。
- tools/translation/export_sol_full.py：核对冻结结果、修订及补译后导出正式词表。
- tools/patch/install-full.ps1：游戏关闭后备份安装；tools/patch/package-full.ps1：按白名单生成个人备份ZIP。
- 线索运行别名/组合规则由prepare_lead_followup.py维护（--runtime-cases生成八组冻结TSV）；地图白名单由prepare_map_ui.py维护。UI_FOLLOWUP模式必须同时开启JOURNAL并提供LEAD_CASES。时间线当前loop=0，历史索引向过去递增；Previous加1、Next减1。真实时钟纪元为06:00。反射须精确签名，未参加/未来项不提前调用Details；缺scene明确跳过，不能造零Changes。完整接口与中断恢复见本轮文档。
- tools/patch/run-toggle-probe.ps1：默认菜单/F8后台验证；逐档模式使用 ELSINOREHAN_PROBE_SETTINGS_OPTIONS=1，并设置正式译文、字形、冻结缓存用例路径。详细运行契约见源码与ui-audit.md。
- 资料模式ELSINOREHAN_PROBE_JOURNAL=1与逐档模式互斥；run-headless-probe会强制真实资料断言，COLLECTED不是成功。文档资源通过实际展示入口及局部重载验证，不冒称世界内搜寻物件或物理键盘E2E。日志连续源白名单是当前正式源快照，新源需更新，勿盲跑早期补译生成器覆盖手工规则。
- 下一步按用户实际遇到的漏译、错译和排版反馈修订。优先确认源字段、实际组合及拦截路径；不要重译全文作为修补方法。
- 公开分享尚未完成：当前arialuni_sdf_u2018字体的再分发许可未核实，正式发布应换授权明确且兼容Unity2018/TMP的字体并验证，补齐第三方许可、安装/卸载说明和干净目录安装验证。当前ZIP是个人备份，不称正式公开发布包。
- 百炼四模型比较已停止，旧结果只作历史证据，不恢复调用、不要求新Key。公开业务空间地址在 translation/provider.json，密钥仅在被忽略的api-key.txt，不输出或打包。套餐实际CLI用量见sol-full.md，不能从token数编造周额度扣减百分比。

历史参考 PipistrelloHan 的实现差异与翻译工具调研保存在任务文档；其IL2CPP/BepInEx6/多语言CSV方案不能直接套入本游戏Mono x86现场。
