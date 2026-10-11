# 贝尔纳多友谊回应校订

2026-10-11，用户日志截图反馈“至少，我还有这个”含糊。真实 `scenes` 资源、`FLAVOR_BernardoPerformance` 第16699行是 `There's that, at least.`，紧接奥菲莉娅“但我会永远——永远是你的朋友”。这里的that承接友谊承诺，不指物品。

原译“至少，我还有这个。”改为“至少，我还有你这个朋友。”，保留at least的退而求其次语气。完整资源核查含贝尔纳多担心秘密曝光、奥菲莉娅承诺支持及后续称呼询问，不从孤句补写新的关系、身份或动作。准确旧值、源SHA和资源来源登记在 `translation/supplemental/dialogue-context-corrections.json`，冻结输入、raw及outputs不改。

`tools/translation/prepare_bernardo_friend_followup.py` 从真实资源再生5项检查：裸句、说话人日志、五句相邻语境及通知前后组合。与上一轮22项幽灵消费者合并后，27项真实XUnity递归消费者及15项导出检查通过；17,041词条、155规则不变，动态字典哈希不变。

通过 `package-full.ps1 -PendingInstall` 更新37文件个人候选包，目录与ZIP逐项一致，包含上一轮“一场更大的游戏”及本轮友谊回应。当前候选哈希见 [本轮核验](../../../runtime/evidence/bernardo-friend-followup-verification.json)，旧候选与字体调研的来源SHA保留各自快照。

尚未安装，未操作主游戏或存档；没有更换字体，不称完整游玩E2E或像素验收通过。
