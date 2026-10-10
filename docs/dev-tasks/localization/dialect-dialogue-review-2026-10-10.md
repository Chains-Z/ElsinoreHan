# 其它角色方言与口语定向审校

根据用户要求，接续伊尔玛审校，提前核对其他角色的非标准英语、俚语及口语句法。已安装六处定向校订，插件仍为1.4.0，17,027条、138规则；个人ZIP同步。

## 范围与判断

从全部TextAsset剧情资源筛查43个发言角色、17,061次发言、15,181个不同角色/源句组合。词形只用于选择人工审校候选；bloody可能指真正血腥，ye可能是经文古语，不能自动判错。带标记的非伊尔玛句子416条。

最终逐句审校621个角色/源句组合：马塞勒斯228条、格蕾丝199条；卫兵、匪徒、海盗、村民等八个配角角色100条；其他角色命中的特殊表达94条。前两人的全部对白均审读，包括未命中方言标记的普通句子。范围不等于其它所有人物全文人工审校。局部相邻资源上下文可能包含互斥分支，不能冒充完整剧情游玩。

马塞勒斯使用yeh、yer、canna、en't、kin、wot、I dunnah等；格蕾丝使用yer、yeh、canna'、wiv'、wee、lass、nary等。多数已有自然正确译文，没有新发现把方言称呼误作人名的Maike型错误。海盗的better'n、more'n、th'等省音、卫兵的ain't及Dunnah也已正确处理。布莉特的'Feely昵称17处均已译为菲莉，保留。

粗俗称呼、双关、结巴和反讽依实际语境保留，不一刀切转换为严谨书面语。用户指定的“资历最老”及最终整句不改。

## 六处校订

| 稳定ID | 调整 | 理由 |
| --- | --- | --- |
| p05562-a4c4a7fd5356 | 互相掐死 → 斗得不可开交 | at each other's throats表激烈争斗，不指定掐脖子的杀法 |
| p05586-ef4cb9c216d0 | 王室小麻烦 → 王室烦人精 | Royal Pain是挖苦称呼，pain指烦人的人，保留王室笑点 |
| p08805-aead12d61d70 | 聊聊故事 → 讲讲故事 | yarn在海上喝酒讲经历的上下文中指故事；不额外添加虚构判断 |
| p08933-603a5ec7100a | 不必要的死人 → 没必要闹出的人命 | death指死亡事件，改为自然口语 |
| p06104-e5f94d12cb02 | 那人可能是谁都不一定 → 那人是谁都有可能 | 修正混杂的中文语序，保留身份不确定 |
| p03228-16f33652e512 | 我们来看看你还好吗 → 我们来看看你有没有事 | 陈述句的间接疑问不硬接吗，保留前来问候的意思 |

全文及准确旧译文、来源资产/场景/行号和原文SHA位于translation/supplemental/dialect-corrections.json。校订在导出层应用于已有稳定ID，不修改冻结输入、模型响应或原始资源。

词义依据：[Cambridge习语](https://dictionary.cambridge.org/dictionary/english/at-each-other-s-throats)、[Cambridge pain](https://dictionary.cambridge.org/dictionary/english/pain-in-the-neck)、[Oxford yarn](https://www.oxfordlearnersdictionaries.com/us/definition/english/yarn)。词典释义与具体场景判断分开记录。未将异常口语twice a thug over判为确定的固定俚语；上下文存在比较对象，旧译比较虽可能说得过实，本轮证据不足以认定错误，保留。

## 验证与维护

tools/translation/audit_dialect_dialogue.py可再生全资源筛查记录与621项审校选择。每条选择生成单句、真实简称日志及通知前/后双向组合，共2484项真实XUnity递归消费者通过；15项导出治理回归通过。全量重复夹具忽略入Git，来源与范围在runtime/evidence/dialect-source-audit.json，安装及ZIP核验在runtime/evidence/dialect-review-verification.json。

重新生成既有全量日志期望，没有把生成动作当成114,028项重跑通过。本轮没有重新跑重型资料/F8滚动或剧情E2E。通知组合只检查消费路径，不表示实际剧情出现该组合。正式安装使用游戏关闭检查及旧补丁备份，不修改存档、帧率或音量。
