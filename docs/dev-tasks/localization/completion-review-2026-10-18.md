# 当前存档进度与终局验收口径

按用户要求只读核对当前存档、原游戏逻辑位、线索与结局UI的消费代码。原始审计位于本机被忽略的`runtime/build/save-completion-audit/`，含`report.json`、`source-evidence.json`、原代码IL及`save-protection.json`。没有启动游戏、触发业务加载、修改存档、采用结局、建立通关备份或访问Steam账户成就。

## 当前状态

第32轮，正常主游戏状态。存档8个文件前后路径、数量、大小、mtime及SHA256完全一致。

| 项目 | 只读核查结果 |
| --- | --- |
| 普通书页结局解锁 | 11/11 |
| 特殊主线结局解锁 | 0/2，`END_Revenge`与`END_JoinQuince`均未解锁 |
| 正式采用后完成结局叙述 | 0，13个持久`viewedEnding`均为false |
| 已烧毁普通命运 | `numberEndingsBurned=0` |
| 日记线索 | 19/20完成，只有`Quince_Story`最后的`quince_complete`未完成 |

玩家此前已经经历普通结局对应的支线、观看解锁事件与命运解锁页；这与在书里正式采用后完成整段结局叙述不同。不能把`viewedEnding=false`解释为玩家没有看过相关剧情。

`GuiUtils.IsLeadComplete`读取线索最后一行的`leadActive`。戏剧大师末行需`playerAttended(SC_NOESCAPE_Ghostlastmanifest)`，即亲自在场经历幽灵最后现身。当前已拥有`EvilQuince`，但幽灵与哈姆雷特尚未获得针对奎因斯的相应信息，相关演出/后续事件计数为0，`ghostdestroyed=false`。

## 接下来的顺序

1.为补丁结局正文验收，可先逐页正式采用11个普通命运，完成叙述与片尾后继续返回。已采用的页会永久烧毁，不能再次采用；如需重测，要另保留验收检查点。
2.将现有`EvilQuince`情报告知哈姆雷特与幽灵，推进针对奎因斯的演出、其后PerfectDay流程，亲自在场完成幽灵最后现身，以收尾戏剧大师线索并开放烧书。
3.若要分别测试两个特殊终局，在普通结局验收及戏剧大师收尾后、烧整本书或进入升格杀戮流程前保留分支检查点。两条路线分别完成，不能把它们理解为普通书页上的直接二选一。

以上普通11页全部采用是全结局正文验收的建议顺序，不是最终主线的统一门槛：升格路线的`WITCH_InitialKickoff`要求`numberEndingsBurned>=4`、`ghostdestroyed`且尚无`NotNeeded`，随后仍需独立杀戮/升格流程；`SC_WITCH_ASCENSION`另检查12名指定人物死亡与`demontripped`。烧书入口在幽灵最后现身后开放，不要求11页全部先采用。

计数细节：`EndingSceneUI.Activate`解释整段结局脚本时先执行计数加1，`GoToCredits`稍后登记持久`viewedEnding`与本轮临时`endingConfirmed`，再由片尾激活保存。下一轮`endingConfirmed`可能清除，因此不能只根据这个临时字段判断是否曾采用。本档持久字段和计数也都为0，结论明确。

## 特殊终局与百分百的区别

- `END_JoinQuince`后继续，会处于全员死亡状态，`EndingBookObject.Initialize`关闭书本渲染与碰撞器。
- `END_Revenge`后继续，书页统一判为烧毁，奎因斯处于`shattered`状态，并移除四项关键情报。
- 两者的继续功能都不是返回选择前。恢复同一检查点分别验收两个分支，会覆盖第一分支后来写下的本地完成标记；可以记录两条都实际验收过，不能称同一存档同时保留13项完成标记。
- 在已核查的当前存档及结局、线索UI消费代码中未找到统一官方100%指标，未读取Steam账户成就。可分项报告11普通命运、2特殊终局及20线索；不能据此承诺全成就或穷尽对白。

对本补丁，合理的游玩验收目标是主要结局、线索和有代表性的关键分支，再以资源/词表完整性与组件回归补足。当前17,068条词表的导出治理通过，不等同逐条对白人工审校；无需把所有对白排列组合都玩遍才能完成这轮定向维护。
