# 波洛涅斯离开前安排对白校订

状态：候选已验证，尚未安装。用户游戏正在运行，本次不覆盖主游戏补丁、不启动游戏、不访问存档。候选保留此前待安装的首次“盘问”校订，见[候选核验](../../../runtime/evidence/polonius-preparations-verification-2026-10-18.json)。

## 原文与校订

`p07685-58c2ae910d95`，真实`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`，`leave_decision`第20959行，角色波洛涅斯。原文：

> Necessary preparations ought to be made—but of course, there is little use in me making them, as I owe the court nothing further.

旧译“必要的安排还是该做——不过，我当然也没什么必要去做了，毕竟我对宫廷已不再负有什么义务。”。用户确认改为：

> 临走前总该做些安排——不过，我已不欠宫廷什么了，再由我来操办，也没什么意义。

保留先说应当准备、随后改口的语气，将little use译为“没什么意义”，owe the court nothing further译为“已不欠宫廷什么”。原文没有明确准备事项，不擅自补成公文交接、辞职手续或不愿收拾行李。前句为尽快启程，后句哥哥接话收拾行李并让雷纳尔多安排马车。

通过`local-corrections.json`的`apply_at_export`应用，保留准确旧值、原文哈希及资源来源，冻结输入、raw、outputs和审计未变。

## 验证与范围

- 4项真实XUnity递归消费者通过，覆盖裸句、对话框真实行高封套、日志单句及相邻对白；16项导出治理测试通过。
- 相对上一“盘问”候选仅本条变化，原有全部其它条目不变；17,068词条、157规则及中文字集合不变，无需重建字体或插件。
- `package-full.ps1 -PendingInstall`生成候选，40文件与ZIP逐项一致；相对已安装包仅正文词表和候选状态说明变化，相对上一候选仅正文词表变化。
- 本轮仅是词表与组件验证，不代表真实对话UI像素、物理F8或完整剧情端到端验收。后续须确认游戏退出并使用安装器更新。
