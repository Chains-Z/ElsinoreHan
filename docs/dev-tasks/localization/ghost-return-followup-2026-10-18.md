# 幽灵返回方法答复校订

状态：候选已验证，尚未安装。未启动或操作主游戏，未访问存档。见[候选核验](../../../runtime/evidence/ghost-return-verification-2026-10-18.json)。

真实`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`，`POSTEND_Return`第29532—29533行：

> Can you help me? Do you still know how to return?
>
> Of course I do. But why would you consider such a thing?

`do`承接`know how to return`，是在确认知道回去的方法，并未答应帮忙。用户确认改为：

> 当然知道。可你为什么会有这种念头？

裸源`p10431-b4d623ece42b`原本译为“当然知道。但你为什么会有这种念头？”，实际幽灵整体斜体源`a00358-78e318dc7261`却译为“我当然会。但你为什么会考虑这种事？”。两条通过`local-corrections.json`统一，保留实际源的斜体；准确旧值、源哈希和出处均已记录，冻结输入、raw、outputs和审计未改。

18项导出治理测试与5项真实XUnity递归消费者通过，覆盖裸源、斜体运行源、对话框行高封套、日志单句及问答组合。17,068词条、157动态规则和中文字集合不变，复用已安装字体与插件的核验；没有重跑未改变的字体或页面验收。

`package-full.ps1 -PendingInstall`生成待安装候选，40文件与ZIP逐项一致。本轮只验证词表及组件，未声明实际画面、物理按键或完整剧情端到端通过。
