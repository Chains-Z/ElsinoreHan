# 进入结局前的谢幕对白审校

2026-10-18：已核查11个普通结局的谢幕分支、共用开场和收尾，共13个脚本块、449段发言、418条不同的实际运行源。修正15处发言，对应17条资源或运行词条；另按玩家确认修正婚姻结局的两段表达。本轮累计19条译文变化，已通过安装器安装。

## 完整阅读入口

- [谢幕完整中英对照](curtain-call-texts-zh-CN.txt)：中文在上、英文在下，按结局标题区分，保留互斥条件与共用段落引用。449段包含纯省略号，不能理解成一次连续播放的剧情。
- [13个结局正文对照](../endings-review-2026-10-18/ending-texts-zh-CN.txt)：同步了玩家确认的“暂时缓解这些苦痛”。
- [逐段审查清单](../../../../translation/supplemental/curtain-call-review.json)、[精确旧值校订层](../../../../translation/supplemental/curtain-call-corrections.json)、[候选核验](../../../../runtime/evidence/curtain-call-verification-2026-10-18.json)、[上轮安装核验](../../../../runtime/evidence/curtain-call-install-verification-2026-10-18.json)、[公媳称谓补改安装核验](../../../../runtime/evidence/inlaw-install-verification-2026-10-18.json)。

## 修正内容与理由

| 分支 | 修正 | 原因 |
| --- | --- | --- |
| 放弃挣扎、女王、海盗、奥赛罗，4处 | “上次我们离开奥菲莉娅时”→“上回说到奥菲莉娅时” | `When we last left Ophelia`是剧情回顾，不是众人曾经离开女主。其余7个分支已经表达了回顾，保留。 |
| 放弃挣扎 | “我们所有人都是如此”→“对我们每个人来说，都是如此” | 她是每个人生命里的美好，而不是说众人本身都属于美好之一。 |
| 海盗，实际斜体源 | “今后你仍须活下去，梦里会有……”→复用资源版“此后活着的日子里，那些被你留下的面孔会一直出现在你的梦中” | `must live dreaming`指此后的生活离不开这些梦，不另加必须活下去的劝告。 |
| 奥赛罗，实际斜体源 | “几段美好年华”→“几年美好时光” | `a few good years`有明确的年数范围；资源版已经正确，运行版复用它。 |
| 女主独自离开 | “所以……才……”→“所以……” | 下一句是“你一定要活下去”，原句留下无着落的“才”，破坏了衔接。 |
| 女主独自离开 | “别像我。别像我们这些人”→“不像我。不像我们这些人” | `Not like me`继续描述她应当寻找的人，属于说话者的自省，不是对女主的命令。保留“全心全意爱你”。 |
| 举家流放 | “她的家人”→“她一家人” | 选择包含女主自己，结局中她与父兄共同流放。 |
| 举家流放 | “重新考虑对我的感情”→“重新看待我” | 波洛涅斯在衡量君主对自己的政治评价，而不是亲密感情。 |
| 所有人生还 | “蹬着腿、不甘心地进坟墓”→“不甘不愿地咽气” | 保留不肯服输的调侃，不把习语中的`kicking`硬译成进坟墓时蹬腿；保留“更多”的斜体。 |
| 福丁布拉斯统治 | “一个国家的全部认同”→“一个国家的身份认同” | `entire`修饰国家，`identity`指国家身份认同，原搭配不准确。 |
| 哈姆雷特婚姻谢幕，裸源和实际斜体源 | “独一无二的片刻”→“奇异的一刻” | 按玩家反馈，`singular`在生者亡者短暂相聚的场景取奇异之意；不扩写为奇幻世界。两条源分别核对旧值。 |

## 截图反馈的两项决定

用户最终决定使用“公公”和“儿媳”，不采用生僻的“家翁”。原文`father-in-law ... his daughter`指女主与老国王通过婚姻形成的亲属关系，现译“自己的女儿”会误导为亲生女儿。裸源与幽灵实际斜体源分别核对旧值后统一为“奥菲莉娅。但愿我能给你一个慈爱的拥抱，像公公疼爱儿媳那样。”，保留实际外层斜体。母女、父女、兄妹之间自然的“爱”，以及实际恋爱表白均保留，没有统一改成温情或友谊。

婚姻结局原文为：

> That this life is suffering from start to finish, punctuated by fleeting moments of bliss. Love merely stops the bleeding a while.

前一句没有“伤口不断流血”的明确描写，`punctuated by`也不是穿刺、流血。最后一句才突然引入止血比喻。曾提出补出隐含伤口的候选，玩家认为中文仍然跳跃，最终明确选择优先自然中文，定稿为：

> 她说，人生从头到尾都是苦难，幸福只是转瞬即逝的点缀。爱，也只能暂时缓解这些苦痛。

这项意译舍去止血意象，保留爱情只能暂时减轻苦难的限制；没有宣称原文前一句已经写出了伤口。见[校订层](../../../../translation/supplemental/ending-marriage-corrections.json)。

婚姻结局最后一句`After all, it's a beautiful day for a wedding.`按玩家确认改为“毕竟，今天这么美，正适合举行婚礼。”。`beautiful`呼应前文阳光和婚纱的场景；保留原文的收束语气，不把结合上下文读出的自我安慰直接增写进正文。

## 来源、治理和验证

- 从真实`resources.assets`重新提取脚本，对照原始发言顺序、角色、源哈希和实际标点替换；449段实际源均在程序集字符串审计中找到。13个脚本块与原审查顺序一致，11个标题匹配真实结局元数据。
- 扫描全部脚本的共源引用，17条谢幕校订在已审场景之外没有额外对白引用。资源裸源与幽灵实际斜体源分别核对，不用一个版本替另一个兜底。
- 冻结输入、模型响应与输出不变。新校订绑定源哈希、来源和准确旧译；先前431项love审查与13结局审查保持快照，由精确后续覆盖更新消费者预期和阅读稿。
- 574项谢幕、642项love/归来、407项结局正文及79项受影响的既有日志消费者通过。使用真实XUnity解码、逆序首匹配及递归上限64，不改变规则来适配测试。
- 上轮17条新译的定向对照在旧词表下全部不符、在候选下全部通过。本次公媳称谓另有6项正文/行高/日志定向对照，旧词表6项不符、新词表6项全部通过，并复核6项受影响的既有夹具。19项导出治理及4项阅读覆盖保护测试通过。
- 一个既有整场压力夹具还保留了此前已安装的“三句谢幕”旧预期；用上轮词表和原预期同样能重现失败，再依据既有准确旧值校订更新夹具。没有为此修改新译或消费者逻辑。
- 词条仍为17,069，动态规则157，插件1.5.11及7,661字形字体不变；本轮新增所需字“缀”已存在于现有字体。40文件候选ZIP逐项核验。

以上是资源核查与真实离线消费者组件验证，不称游戏内逐分支实测或端到端通过。文本校验不访问存档；安装时仅只读核对保护快照。主游戏已安装累计19条校订，38个运行文件与候选一致，40文件个人ZIP逐项核验；原游戏4文件及8个存档的哈希、修改时间、大小和数量未变，没有启动游戏或保留旧补丁备份。

## 复现入口

```powershell
python tools/translation/export_sol_full.py
python tools/translation/prepare_curtain_call_followup.py
python tools/translation/prepare_all_endings_followup.py
python tools/translation/prepare_love_context_followup.py
./tools/translation/verify-recursive-ui.ps1 -TestsPath translation/supplemental/curtain-call-tests.json
./tools/translation/verify-recursive-ui.ps1 -TestsPath translation/supplemental/all-endings-tests.json
./tools/translation/verify-recursive-ui.ps1 -TestsPath translation/supplemental/love-context-tests.json
./tools/patch/package-full.ps1 -PendingInstall
```

各次消费者调用必须顺序执行，避免同时覆盖同一个验证器可执行文件。本轮安装已完成；以后重建候选仍须等玩家退出游戏并通过安装器，安装后再生成不带`-PendingInstall`的已安装包。
