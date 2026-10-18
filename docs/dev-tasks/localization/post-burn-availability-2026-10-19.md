# 烧书后结局选择与状态文字只读核查

结论：完成 `END_Revenge` 后，正常玩家书页入口不能再采用11个普通命运。这是原游戏的状态限制，不是漏译。两处结局界面均把所有普通命运视为已烧毁，隐藏相关选择按钮；烧书按钮也隐藏。已解锁页仍显示原有简介，没有另换一段烧书后专用的“不可选”提示。

本次未启动游戏、读取或修改玩家存档、安装补丁或修改共享词表。只读提取原程序集与资源，核对当前中文和已安装词表，并使用真实 XUnity 离线消费者验证。证据见 [完整审计 JSON](../../../runtime/evidence/post-burn-availability-audit-2026-10-19.json)。昆斯 `POSTEND_QuinceBookBurned` 的31句对白由[另一专项](post-burn-dialogue-2026-10-19.md)审查，本报告覆盖结局界面及烧书后晨间14次发言。

## 原游戏如何限制选择

`EndingSelectUI.Activate` 按 `Ending.IsVisibleInBook` 取出11页；字段虽然名为 `UnlockedEndings`，实际并不只保留已解锁页。`isEndingBurnt` 在两处界面中完全同义：

```text
burnt = viewedEnding(END_Revenge) || viewedEnding(当前结局)
```

因此，烧书前已经采用的普通结局本来就不能再次采用；烧书后，即使某个普通结局尚未采用，也会统一判为烧毁。原游戏没有在这里撤销 `unlockedEnding` 或把简介删除。

| 普通页状态 | 说明文字 | 重温按钮 | 烧毁叠层 |
| --- | --- | --- | --- |
| 未解锁、未烧毁 | `这个世界尚未成为现实。`，保留原斜体 | 隐藏 | 隐藏 |
| 未解锁、已烧毁 | 同一未解锁提示 | 隐藏 | 显示 |
| 已解锁、未烧毁 | 该结局原有简介 | 显示 | 隐藏 |
| 已解锁、已烧毁 | 同一结局原有简介 | 隐藏 | 显示 |

准确分支如下，完整原IL及偏移保存在审计 JSON 的 `key_methods`：

- `EndingSelectUI.populate`：`IL_006c` 调用烧毁判断；`IL_0073` 起控制 `BurntOverlay`；`IL_0089` 起判断解锁。已解锁分支写入 `Ending.Description`，并令 `RevisitEndingButton` 的显示状态等于 `!burnt`；未解锁分支在 `IL_00ec` 写入上述固定提示。
- `EndingSelectUI.Activate`：`BurnBookButtons` 仅在 `unlockedEnding(END_Revenge) && !viewedEnding(END_Revenge)` 时显示。烧书完成后整组隐藏，不再弹出烧书确认框。
- `GameOverUI.Activate` 的普通确认页分支：仍写入原有标题与简介，按同一烧毁判断显示叠层；`ConfirmEndingButton` 仅在 `SceneAccessedFromEndingUi && !burnt` 时显示。`FateUnlockedHeader` 还要求当轮刚解锁且未烧毁；没有替换成新的烧毁说明。
- `GameOverUI` 的内部 `ForceConfirmEnding` 脚本分支会提前直接选择结局。本报告的不可选结论指正常玩家书页按钮，不扩大为所有内部脚本调用都被禁用。

书页仍列出11页，不等于玩家能在任意业务状态下打开书。`EndingBookObject.Initialize` 仅在主游戏、持有书且尚未完成 `END_JoinQuince` 时开启书物件的渲染和碰撞；`Interact` 还要检查 `BookEnabled`，上层交互准入仍须满足。本次没有运行实际导航，因此不宣称烧书后任何时刻都能打开。

## 文本命中与晨间分支

共94项可见源核对，包含重复字段和两次省略号，不是94条独立新增译文。全部词汇源精确命中当前导出词表，且对应编码行已存在于主游戏安装的 `ElsinoreHan-Sol.txt`：缺词0项、安装行差异0项。每项均记录英文键、SHA256、中文、词条ID及资源字段/程序集偏移；静态按钮与悬停文字还逐一回读 `level1` 的长度前缀与UTF-8原字节，核对来源。

覆盖范围包括13个结局的标题关键词与简介、未解锁提示、重温确认框、烧书确认框、普通结局确认框、按钮及书物件悬停文字。特别核对了容易漏采的双按钮首项 `Choose This Ending` 和 `Hand of Dionysus`；脚本对这两项及全部预期静态标签设置集合断言，不能仅靠总数变化宣称覆盖。烧毁图片中的 `Sacrifice/for` 继续沿用[已安装的叠层修复](ending-burnt-paper-followup-2026-10-18.md)；本次核对其中文源词，没有重复进行像素验收。

晨间场景的实际标记为 `Spine_OpheliaHamletStarter`，由最近的真实场景标记读取；`SC_SPINE_OpheliaHamletStarter` 是事件ID。烧书分支位于真实 `scenes` 第510–555行，共14次发言：12句有词汇正文、2次纯省略号，全部已有翻译。

其中 `What? I--` 的真实编译运行源为 `What? I—`，两种键均精确命中“什么？我——”。每句运行源都回查当前 `Assembly-CSharp.dll` 对应生成方法的 `ldstr` 与偏移；另外验证90%行高对话框、单条日志以及首次/四种后续随机路径的完整日志组合。没有把互斥台词串成一条实际剧情，也没有把省略号误判为漏译。晨间译文不在本次修改范围。

烧书后的状态初始化还会设置 `shattered(quince)`，并移除 `EvilQuince`、`NotNeeded`、`Responsible`、`Playmaster` 四项持有情报。资源中有两份同名 `smalltalk`：旧资产 `e0618e4f…` 含旧 `ST_Quince_*` 映射，主游戏资产 `0122007f…` 把 `shattered(quince)` 指向 `POSTEND_QuinceBookBurned`。审计保留两份资产的精确哈希和引用，不把旧资源映射当成当前31句的替代来源。`schedule` 中六处 `not viewedEnding(END_Revenge)` 及音乐条件也已列出；它们限制既有事件/音乐，不产生新的结局按钮文案。

## 验证层级与复现

- 原IL状态重放：11页 × 解锁真假 × 烧书结局完成真假 × 当前页已采用真假，共88组状态。每组严格解释两处原 `isEndingBurnt` 方法的真实指令和跳转，共176次，全部符合布尔公式。`unlocked` 不参与烧毁判断，保留在矩阵中用于审查书页显示条件。按钮显示条件来自原 `populate/Activate` 静态核对。
- 真实 XUnity 离线消费者：127项全部通过，使用实际安装的 `RegexTranslationSplitter/ParserResult`，维持逆序首匹配及递归上限64。消费者结果、夹具SHA256、验证器源码SHA256和实际插件SHA256均记录在 JSON。
- 未进行真实Unity组件运行、物理按键、页面像素或剧情E2E；本次结论为原逻辑与文字消费覆盖，不能扩大为全部状态的实际画面均经过人工游玩。

复现命令在项目根目录执行，使用 PowerShell 7；生成的IL缓存和文字夹具位于被忽略的 `runtime/build/post-burn-availability/`：

```powershell
& tools/translation/audit_post_burn_availability.ps1
python -X utf8 tools/translation/audit_post_burn_availability.py
```

原文件指纹如下，完整路径、词表与消费者指纹见 JSON：

| 文件/资产 | SHA256 |
| --- | --- |
| `Assembly-CSharp.dll` | `69e348fc4180302fc38724ec8ee5609e7fc94b59622dcab881ce44cc0b2fe6af` |
| `Elsinore.dll` | `b2e9262cad8d73b3e0afe643277560be5e5e04f01ded55573755ea56b17b8bd4` |
| `resources.assets` | `6d0ae1f735d95db40b836cedfc25e92143aa3727fee7bcd71e0cb319320961fd` |
| `level1` | `346dbdd37e25e69de3c470a2cd138630bd68cd6fe3c66e8b8770eed043945ef2` |
| `endings` TextAsset | `9e4951e02fa91d220df788335fff28df5d15f2f376dc294c338da18d21b2abd1` |
| 主游戏 `scenes` TextAsset | `6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a` |

在上述范围没有发现新增漏译或需要修补的状态提示。玩家当前已经全解锁、全采用，无法再自然看到未解锁页，仍可通过原分支、真实源字节和离线消费者核查该提示，不必为此修改玩家存档或重玩。
