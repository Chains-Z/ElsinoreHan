# 乔特鲁德母子感情对白校订

状态：用户确认修改，已导出并生成待安装候选包，尚未安装到主游戏。插件保持1.5.9。见[候选核验](../../../runtime/evidence/gertrude-family-verification-2026-10-17.json)。

## 原文与校订

`p07484-4211bd063067`，原文为`You tore me from my son. My son from his <i>father.</i>`。来源为真实`scenes`资产的`FLAVOR_GertrudeQuestionClaudius`第20408行，资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`。

乔特鲁德在得知克劳狄斯杀害老哈姆雷特后斥责谋杀与谎言，前一句为`But murder—cold murder—that was wrong. You took my family away from me.`。按用户指出的感情语境，前半句表达母子关系被撕裂，后半句表达儿子失去父亲。旧译“你让我与儿子分离”容易被理解为两人被迫分开生活。按用户确认改为：

> 你毁了我们母子的感情，也让我的儿子失去了他的*父亲。*

保留原文父亲部分斜体；不补写具体分离动作。通过`local-corrections.json`的`apply_at_export`应用，记录准确旧值、来源及源哈希，冻结输入、raw、outputs与审计保持不变。

## 验证与范围

- [消费者夹具](../../../translation/supplemental/gertrude-family-tests.json)绑定真实角色、场景与行号，覆盖裸句、乔特鲁德日志及同场景相邻对白。3项真实XUnity逆序首匹配、递归上限64的组件消费者通过，15项导出治理测试通过。
- 导出相对上次结果、候选相对已安装词表均精确改变本句；17,067词条、157动态规则及全部中文字集合不变，无需更新字体。
- 通过`package-full.ps1 -PendingInstall`生成候选包，40文件与ZIP逐项一致。相对当前已安装包仅正文词表及候选状态说明改变；插件、字体、动态词表、配置与许可字节不变。
- 未修改游戏安装、启动游戏或访问存档。本轮仅执行离线来源与组件核验，未执行UI像素或完整剧情端到端验收。
