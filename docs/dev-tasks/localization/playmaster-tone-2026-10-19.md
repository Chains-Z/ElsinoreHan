# 恢复戏剧大师与轻蔑语境处理

状态：用户确认后完成候选校订，尚未安装。插件1.5.15、17,069词条、157规则、7,661字形不变。本轮相对上一候选33个目标变化；撤回大部分“戏班班主”改称后，累计561个词条与已安装版不同，并非本轮新增561处正文改写。

## 全范围审查

已复核当前词表全部33个包含`Playmaster`的准确英文键及对应对白上下文，包括大小写、资源标点和编译源。33是词表键数量，包含重复变体，不能称为33处独立剧情。逐项源、改前／改后、策略和对白出处见[完整记录](../../../translation/supplemental/playmaster-tone-review.json)。

其中30个继续使用“戏剧大师”；三句用`little countryside`或`little traveling`轻视其身份的对白，按语境使用“艺人”。此外复核了波洛涅斯的丑角说法、马塞勒斯的激将、哈姆雷特的惊疑与客套、昆斯的谦称和操纵演出的叙事用法，未把所有批评或惊疑都改成职业贬称。

| 角色／英文 | 新译文 | 判断 |
| --- | --- | --- |
| 王后：Peter Quince? This little countryside playmaster? But I don't understand! | 彼得·昆斯？就那个乡下来的艺人？可我不明白！ | 用艺人承接轻视其出身及身份的语气 |
| 贝尔纳多：Peter Quince? This little countryside playmaster? But I don't understand. | 彼得·昆斯？就那个乡下来的艺人？可我不明白。 | 与王后的平行对白一致，保留句末差别 |
| 克劳狄斯：Quince... that name is familiar. Ah. You mean that little traveling playmaster? | 昆斯……这名字耳熟。啊。你是说那个四处巡演的小艺人？ | 保留巡演和轻视意味 |
| 波洛涅斯：The Playmaster's job is to play the fool. If he was not strange, he would be a poor fool, would he not? | 他这个戏剧大师，本来就是扮丑角的。他要是不古怪，岂不是连丑角都演不好了？ | 句法明确是在谈昆斯这个人，不像给所有戏剧大师定义职业 |
| 马塞勒斯：And what of you, Playmaster? Are yeh gonna sit around an' let a bunch of girls call yeh useless? | 那你呢，戏剧大师？你就坐在那儿，任由一群姑娘说你没用？ | 激将与打趣能够自然使用称号，仅恢复称谓 |

人物介绍有`leader of a traveling troupe of players`，波洛涅斯又称它为`one-man 'acting troupe'`，布莉特说他总是独自演出。保持这些原文信息，不为称号统一而改写人物介绍。另核对资源提取12条记录与程序集提取23个源，玩家文本均有对应键；唯一排除项为内部条件`hasSeen(quince,Playmaster)`。

全局采用“戏剧大师”，是保留角色称号气势的翻译选择；普通指代可按具体语境处理。

## 导出与验证

旧“戏班班主”阶段的校订和派生合同保留历史快照。三个已绑定的规范译文直接恢复“戏剧大师”，自动同步六个资源／运行键；其余27个词条通过[新校订层](../../../translation/supplemental/playmaster-tone-corrections.json)承接准确旧值、源哈希和来源。没有改动英文匹配键或运行规则。

- 129项翻译治理检查通过；称号范围检查允许准确的三处语境例外，并逐字核对上述五句。
- 3,414项本轮派生消费者、4,612项阅读和组合回归通过；完整阅读稿与夹具同步。
- 实际XUnity解析最终字典17,069条全部通过；改前／改后的英文键、稳定ID和顺序逐字不变。
- 708组格式变体全覆盖：707组一致，1组仍是既有`I do.`语境例外；33条显式别名无失配。
- 无新增字符；插件、字体、动态规则哈希不变，40个候选包文件与ZIP逐项一致。

见[候选核验](../../../runtime/evidence/playmaster-tone-verification-2026-10-19.json)。未启动或操作主游戏，未访问玩家存档，不称游戏画面或剧情E2E通过。
