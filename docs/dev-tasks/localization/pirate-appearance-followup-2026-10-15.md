# 海盗外貌观察校订

用户反馈星期六船上海盗的“不好惹”将语气引向性情，认为应表达海上生活形成的粗粝外表。真实英文是`Looks like a tough, scruffy sort. The sea is a harsh mistress, I suppose...`，属于`ST_Generic_Pirate`，并非明确的`weather-beaten`或容貌损伤描述。

结合后句将大海比作严苛女主人的语境，tough采用“粗犷”表达强悍外观，scruffy保留“不修边幅”；不补入“被蹂躏得不成人样”等原文没有的程度。最终译文：

> 看起来是个粗犷、不修边幅的人。我想，大海这位女主人可不好伺候……

真实`scenes_smalltalk`的来源为SHA256 `aef8dad0e3b11e6d39b3c0f537430008bfbb5cf05a11b4ee863c86da42b918dd`第166行，以及同名变体SHA256 `ab46b35e4fae1f3e4f5e6437fde97a9c29d32a4163443af8e8905374d7fac6d1`第165行。原始输入是b0099的`p14494-606bd47163df`，准确旧值、源SHA与两处行号均通过`local-corrections.json`治理层登记。

邻近`ST_Generic_Brigand`也有相同首句，但后句是“我最好别插手”，该语境下“不好惹”有依据，因此不全局替换。`prepare_pirate_appearance_followup.py`生成海盗裸句、角色日志和强盗原译保留三项真实XUnity消费者检查，全部通过；15项导出治理检查通过。仅一条导出词条变化，冻结输入、raw、outputs、审计及此前20条候选校订不变。

新增正文汉字“犷”已在现有7,660字受控字库字符表中，原字体核验已确认该表与实际运行字形一一对应，本轮未重建字体或重跑像素验收。字体、插件、动态规则、配置和许可保持不变。40文件候选目录与ZIP逐项哈希一致，仅正文字典变化。游戏仍运行，本轮未安装、未启动主游戏或测试游戏、未创建备份。详见[候选核验](../../../runtime/evidence/pirate-appearance-verification-2026-10-15.json)。
