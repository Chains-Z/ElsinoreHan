# 幽灵谢幕发言的重复句式与收束校订

状态：离线词表候选已验证，尚未安装；未启动游戏、未读取或操作存档。后续统一候选由主任务维护。

真实`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`，`END_CurtainCall_Resignation`第17211、17213行：

> Do not shy away from the world, as I did. Go into the darkness with strength. Go with purpose.
>
> That is all.

按用户要求保留两次`Go`的重复句式，统一为“前行”，保留第一句进入黑暗的方向，改为：

> 不要像我那样逃避世界。带着力量向黑暗中前行。带着目标前行。
>
> 我要说的就是这些。

此前实际运行译文为“不要像我那样逃避世界。带着力量走进黑暗。带着目标前行。”及“就这些。”。幽灵先承认自己当年的退缩，再让奥菲莉娅有意识地选择未来，随后结束发言；奥菲莉娅沉默后感谢众人。因此后一短句是发言收束，并非新增要求，也不增加对未来的承诺或评判。

全量真实TextAsset核查显示，完整对白`That is all.`精确命中1处，只有此处幽灵；其整体斜体运行源同样命中1处，没有其它角色共享。子串共有7处：另6处分别位于克劳狄斯`That is all. You may adjourn.`的3处发言、哈姆雷特`That is all. No more, no less.`的1处发言，以及布莉特整段指令的2处发言。它们是独立完整源，本轮均未改动。生成器断言精确源的角色、出现次数及子串总数，防止日后来源变化时沿用错误语境。

`local-corrections.json`分别登记两句的裸源与实际幽灵整体斜体源，共4条校订；准确旧值、源SHA256、输入批次和真实场景行号均已记录，通过`apply_at_export`应用。冻结输入、raw、outputs及审计未改，实际运行仍保留原斜体。

[专项生成器](../../../tools/translation/prepare_ghost_farewell_followup.py)从真实资源提取两句与相邻发言，生成[10项消费者夹具](../../../translation/supplemental/ghost-farewell-tests.json)。18项导出治理测试及10项真实XUnity递归消费者通过，覆盖裸句、斜体源、对话框行高封套、日志单句、同人连续发言，以及前句劝告—两句校订—奥菲莉娅沉默和感谢的相邻组合。

导出保持17,068词条、157动态规则，中文字集合及动态词表未变，无需补字。专项源审计保存在本机忽略目录`runtime/build/ghost-farewell/source-audit.json`。本轮仅为真实离线词表消费者和治理验证，不代表游戏画面、物理按键或完整剧情端到端通过。
