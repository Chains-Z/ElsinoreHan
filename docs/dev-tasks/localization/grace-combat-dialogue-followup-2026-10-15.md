# 格蕾丝打斗对白与中文语序校订

本轮根据实际游玩截图定向改两句，候选尚未安装。没有改写冻结模型输出。

## 教匕首的玩笑

源字段 `p08751-b3c5b792c58b`，真实场景 `GRACE_SwordLesson` 第24491行：

> Although yer a wee mite smaller than most—we might have to settle for teachin' you to be annoying rather than dangerous.

旧译“教你怎么惹人烦，而不是怎么伤人”没有交代打斗语境，又把 dangerous 的威胁程度改成了具体动作。新译为：

> 不过，你比大多数人都娇小些——恐怕得退而求其次，教你给对手添点麻烦，还谈不上让你成为多大的威胁。

保留小个子、might 的推测及 settle for 的退而求其次。这里确实用了 annoying，是拿“添麻烦”和“构成威胁”打趣，不能仅因中文不通就认定英文没有这个意思。通过 `local-corrections.json` 的导出层应用。

## 闹出人命的语序

源字段 `p08933-603a5ec7100a`，真实场景 `GRACE_PostMutinyNoDeath` 第24879行：

> If there's one thing I've learned, it's that unnecessary death always comes t'bite me eventually.

按用户指定，将“没必要闹出的人命”改为“闹出没必要的人命”，完整译文：

> 这些年我至少学会了一件事：闹出没必要的人命，迟早总会给我惹来麻烦。

本句已在 `dialect-corrections.json` 有早期校订，故在原专项层修订，保留冻结原译 `previous_target`，增加本次准确旧值及修订历史，不再另加一层冲突覆盖。

## 拇指玩笑核查

`p05583-e12b76cd222a` 来自 `Mutiny_Note_Reveal` 第14907行。`thumb up his arse` 除字面动作，还可粗俗地讽刺无所事事；格蕾丝把习语字面化，笑称砍掉一根后剩一根也够用。不能凭这句推定人物性取向。旧译保留了字面动作和 one 的斜体，但中文没有现成的同义习语，笑点不容易读出。本轮向用户解释，未将说明性的释义硬写进角色台词，也未改本句。

释义依据：[Wiktionary：with one's thumbs up one's ass](https://en.wiktionary.org/wiki/with_one%27s_thumbs_up_one%27s_ass)。这是词义依据，具体笑点是结合本场景砍拇指上下文的判断。

## 验证

两句均从真实 `resources.assets` 的 `scenes` 提取，资源 SHA256 为 `6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`。

- `prepare_grace_sword_followup.py` 绑定准确ID、角色、源场景和行号，生成5项裸句、角色日志及教学相邻语境。
- 5项真实 XUnity 逆序首匹配、递归消费者检查通过；15项导出单元测试通过。
- 正文仅两条目标变化，字符集合不变；字体、动态规则及冻结输入/raw/outputs/audit不变。
- F8真实UI探针使用了教学一句修订后的词表；“闹出人命”语序调整在该探针之后，只重跑本句消费者及导出检查，不冒称最新正文词表重跑过完整UI。

最终候选包与安装状态见[本轮候选核验](../../../runtime/evidence/log-bottom-verification-2026-10-15.json)。
