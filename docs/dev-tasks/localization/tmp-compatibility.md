# 资料正文与动态界面的 TMP 兼容修复

2026-10-09。用户继续游玩后发现：笔记标题已中文，但线索、传闻、人物资料正文、顶部地点时间、时间线事件、互动通知以及可阅读文档仍显示英文。多数源文本已有离线译文；上次字典查询通过不能证明这些控件实际消费了译文。

## 原因与实现

实际安装的 TMP 1.4.0 中，`SetText(StringBuilder)` 和 `SetText(string,bool)` 只更新解析缓冲区，不更新 `m_text`；`text` getter 仍读取旧字段。XUnity 已有相应 Postfix，但只通过 getter 读取原文，读不到最新缓冲区。游戏实际有16处 StringBuilder、4处字符串调用。完整 DLL 哈希与 IL 证据见 [tmp-text-hook-evidence.json](../../../analysis/ui-audit/tmp-text-hook-evidence.json)。

本项目插件1.1.0以 Harmony 前缀将上述输入转交同一个 TMP 控件的正常 `text` setter，并跳过旧缓冲入口。交给 XUnity 的仍是完整英文原文，由它保存原文缓存、加载既有译文及字体；没有预先将游戏数据改成中文，也没有覆盖游戏程序集。这样 F8 可以恢复实际原文。字符串单参数重载转调双参数入口，也受到保护。

对话记录另有拼接问题：`HistoryTracker` 把事件标题、舞台说明、姓名、缩进标签和多条对白拼接，再由 `LogUI` 使用正常 setter 显示。已增加11条限定拆分规则，覆盖标题、换人、缩进、舞台方向和连续对白；连续对白只识别冻结全文源白名单，多行原文优先整句命中，未知姓名和程序标识不逐词拆翻。当前共46条限定UI规则、24条格式规则，总计70条。白名单快照新增源时须更新；不要盲跑早期prepare_ui_supplement.py覆盖手工规则。

还有第二层运行差异：动态控件的 XUnity `TranslateImmediate` 路径不执行富文本与拆分解析；`TryTranslate` 虽能返回组合译文，却不登记完整串。属性 setter 前缀现在先以纯离线API查询，再通过当前5.6.2的 `AddTranslationToCache` 登记完整组合，使用 `Full / scope=-1 / persist=false`。仅内存登记，原 setter 仍接收英文并由 XUnity 保存F8来源；缓存异常捕获后继续原赋值，不阻断游戏更新。该兼容层与当前固定依赖版本绑定，升级XUnity时须重验签名与消费者。

## 后台验证与保护

新探针模式 `ELSINOREHAN_PROBE_JOURNAL=1` 从隔离真实存档进入 HUD、Journal 三页、Timeline、Log 和两份真实文档。文档通过既有展示入口消费 `observable_hamletdiary`、`observable_poldesk` 原资源；不宣称完成了世界内搜寻并点击物件的游玩流程。另以这两份原资源做 StringBuilder、字符串单参数和双参数入口对照。

记录实际控件身份、组合源、缓存译文、中文显示、F8 原文与恢复结果。`COLLECTED` 只说明采集结束；采集为空、原文与译文相同、缓存命中而实际显示不符都不能通过。裸文档源只核对来源和译文存在，实际显示须与带行高封套的真实组合译文精确一致。

测试启动阶段另发现：默认 BepInEx 的 `Application..cctor` 入口可能晚于游戏初始化；游戏会在保护建立前调用分辨率应用，产生窗口。运行器仅在测试期间将加载入口改到 `GameInitialization.Awake`，提前建立存档保护，跳过无图模式的显示质量与分辨率应用。finally 按原始字节恢复加载器配置，窗口守卫继续保留，不用于普通游玩安装或打包。

存档重定向、保存与迁移拦截、原目录哈希/时间/数量核对继续使用。此前已记录的存档写入事故仍见 [save-write-incident.md](save-write-incident.md)。

## 验证状态

修正版已验收并备份安装到正式游戏目录，个人ZIP同步完成；[最终核验摘要](../../../runtime/evidence/tmp-ui-verification.json)记录安装、测试副本和ZIP的插件/两份词表哈希一致，原exe、UnityPlayer、resources.assets、Assembly-CSharp哈希不变。安装备份为runtime/backups/full-9aeae11d4ca44e50859dbc582005cfef。

- 冷启动资料运行 `67326bd795924f60a2b5aa5d96f6cb1a`：真实HUD地点时间、人物名/资料、线索、传闻、时间线事件、日志及两份文档中文显示和F8原文恢复全部通过。
- 两份文档资源哈希、带行高封套的完整组合、StringBuilder/字符串单参数/双参数三入口分别核对；不是仅查询裸文档译文。
- 八个采集阶段均通过真实暂停模式和前后时钟不变检查，避免把实时钟变化误判为切换失败。
- 设置回归运行 `daf2eee559244049bceded4e50c30ed1`：13种值逐档显示、F8原文/恢复、组件溢出、取消不应用通过。
- 43项真实Splitter/ParserResult消费者、15项冻结导出回归、23项探针误报回归通过。
- 两轮原存档哈希、时间与数量均不变；临时探针、appid文件和进程已清理。测试提前入口已按原始字节还原，不进入安装包。

基线 `f42fbdf258944805ac0a4d69eb2bb313`、`646dee29492a4e6ab3430a8a148eb4b1` 未完成资料采集；`a151...`、首次预热修版亦未通过，不作为交付验收。最终采集还含一条Hearsay父页签不存在的DescriptionText诊断，实际传闻条目已单独通过；探针已修正为只比较存在且激活的目标控件。

这套检查不包含像素渲染、物理键盘注入或所有剧情分支。结果及安装状态以本文件最终验收记录为准。

## 人物译名核对

当前采用常见中文译名并统一术语，不严格宣称沿用某一个朱生豪版本。哈姆雷特、奥菲莉娅、罗森克兰兹属于通行写法；朱本的哈姆莱特、奥菲利娅、罗森格兰兹是其他常见异体。主要人物词表检查未发现这些异体交叉混用，当前没有必须改正的明确姓名误译。[国家大剧院人物表](https://static.chncpa.org/m/product-1026164.html)

并非游戏所有人物都来自《哈姆雷特》：开发者确认布莉特、伊尔玛为新增人物，奥赛罗与彼得·奎因斯则来自其他莎剧。[开发者访谈](https://www.gamedeveloper.com/design/road-to-the-igf-golden-glitch-s-i-elsinore-i-)
