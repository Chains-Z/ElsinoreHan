# 哈姆雷特独白断句校订

用户询问礼拜堂对白是否来自原著，并要求修正“死去——不再入睡”。本轮只改 `p01401-bac2254636db` 的断句与对应含义：

> 死去——不过是睡去，如此而已。而我说的睡眠，是让心痛终结，让我必须承受的千般细碎痛楚终结。

游戏英文 `To die—to sleep no more—And by sleeping, I mean to end the heartache, the thousand little pains I have to bear.` 的标点含混。结合[原著第三幕第一场](https://www.folger.edu/explore/shakespeares-works/hamlet/read/3-1/)的独立 `No more` 以及游戏下一句继续以睡眠、梦比喻死亡，将其理解为“如此而已”，避免与后文矛盾；其余游戏现代英语改写的内容保持原有译法，不整段换成其他中文译本。

游戏并未省略独白开头。真实 `Spine_ToBeOrNotToBe` 在1480至1481行分别有 `To be or not to be...` 和 `That is the question.`，已译为“生存，还是毁灭……”和“这是个问题。”；前两句位于独立的首段 `section shout 10`，截图可见部分从第二段 `section 60` 开始。只凭截图不能判断是已滚出视野还是玩家错过首段，不能据此认定游戏删去开头或日志漏译。

校订通过 `local-corrections.json` 的 `apply_at_export` 应用，准确旧值、原文SHA与真实资源来源均记录。`prepare_hamlet_soliloquy_followup.py` 从真实源字段生成3项裸句、角色日志与相邻对白消费者回归；与此前鲁特琴简介3项回归合计6项真实XUnity消费者通过，15项导出检查通过。

仅一条译文变化；冻结输入、raw、outputs与审计不变，中文字符集、动态规则、字体、插件、配置和许可不变。40文件候选目录与ZIP逐项哈希一致；保留此前鲁特琴简介待安装校订。游戏仍运行中，未安装、未启动测试游戏、未创建备份。本轮为定向词表与组件验证，不代表完整剧情E2E或页面像素验收。候选证据见[核验记录](../../../runtime/evidence/hamlet-soliloquy-verification-2026-10-15.json)。
