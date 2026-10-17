# 求婚答复与片段缓存冲突

状态：候选已验证，尚未安装。用户游戏仍在运行，未覆盖主游戏补丁、未启动游戏、未访问存档。见[候选核验](../../../runtime/evidence/proposal-reply-verification-2026-10-18.json)。原版地点不一致按用户要求不改。

## 原因与修复

`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`。`HAMROM_Results`第23587行、正文`p08435-b6fb1c286b88`为`I will.`，已治理译文为“我愿意。”。

真实`DialogueUI.onStartDialogue`先调用`UiStrings.SetLineHeight`，将`<line-height=90%>`加到原句前，再交给文本控件。日志保留同一`DialogueAction.Text`，使用日志专用解析路径。

XUnity从`Spine_LaertesAsksBernardosHelp`第28882及28884行的威胁台词派生`I will.`片段译文，分别为“我就会动手。”和“我会动手。”。完整对话框原文未命中时，Splitter子项查找允许片段缓存，片段优先于裸句正文，导致求婚答复串译。仅核对裸句词表或不加载片段缓存的递归消费者无法复现此问题。

新增一条精确运行别名`<line-height=90%>I will.` → `<line-height=90%>我愿意。`，使完整对话框原文先命中。`dialogue-runtime-aliases.json`记录原正文ID、原文和译文哈希、真实行高封套及来源；导出器要求原文和译文都严格复用同一正文并添加相同封套。没有修改冻结输出、原业务数据、插件或全局片段策略。

## 验证

- 真实XUnity缓存、RichTextParser、RegexSplittingTextParser和ParserResult组件回归6项通过。去掉新增别名时，同一对话框源稳定得到“我会动手。”；加入后得到“我愿意。”。裸句及两条威胁台词的裸句/对话框组合均正确。逆序首匹配、失败不换规则、递归上限64保持不变。
- 对话框、裸句、日志单句与相邻日志4项既有真实递归消费者通过；16项导出治理测试通过，包括拒绝别名封套、原文、译文及来源哈希被篡改。
- 导出仅新增1条别名，原有17,067条逐字不变；现为17,068条、157规则，中文字集合不变，无需重建字体或插件。
- 候选包40文件与ZIP逐项一致，相对此前已安装包仅正文词表和候选状态说明变化。候选不代表已安装，也不代表现场内存、物理F8、像素或完整求婚剧情端到端通过。

## 复验入口

先运行`python tools/translation/export_sol_full.py`和`python -m unittest discover -s tools/translation -p test_export_sol_full.py`。

`tools/translation/VerifyDialogueTokenCache.cs`使用本机.NET Framework编译器，引用`System.Web.Extensions.dll`及`System.Core.dll`。可执行文件四个参数依次为真实XUnity核心DLL、`translation/sol-full-2026-10-09/translations.json`、同目录`dynamic-rules.json`、`translation/supplemental/dialogue-token-cache-tests.json`。

日志及正文组件复验使用`tools/translation/verify-recursive-ui.ps1 -TestsPath translation/supplemental/proposal-reply-tests.json`。候选通过`tools/patch/package-full.ps1 -PendingInstall`生成；安装仍须确认用户游戏已退出并使用安装器。
