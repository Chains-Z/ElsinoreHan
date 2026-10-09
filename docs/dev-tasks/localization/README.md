# 汉化任务分析与交接

## 2026-10-10 当前进展

本轮按实际截图修复线索多段拼接、地图短确认模板、时间线名单/空尾/历史房间及嵌套信念文风。1.3.0、16,861条、121条规则已正式安装，个人ZIP同步；1,538个消费者与真实页面、资源重放、F8往返通过。完整结果和验证边界见 [本轮修复](ui-followup-2026-10-10.md)，前轮字体参数及网格证据保留。以下为前轮和历史记录，不据此重复全文翻译或已停止的模型比较。

## 2026-10-09 前轮进展

最新结果：已用 gpt-6.1-sol 完成112批全文，随后补齐界面源词及文档、哈姆雷特人物资料运行变体；正式离线词表 **16,843条**、F8原文切换和TMP兼容插件1.3.0已安装，当前90条动态规则。最新隔离检查覆盖7组日志、14份文档、14名人物正文与标题、真实分享预览及12份字体单行网格；真实递归消费者56个日志和616个通知通过，粗斜体保留原文。最新交付见[本轮后续修复](runtime-ui-followup.md)，源审计见[ui-audit.md](ui-audit.md)，全文来源及实际套餐用量见[Sol全文任务](sol-full.md)。前轮验证局限和本轮探针修正均保留在后续修复文档中。百炼对比已停止，[取消记录](expanded-trial-cancelled.md)保留发生的调用。以下选型和工期建议为历史记录，不据此恢复付费比较。

本轮用户已授权翻译流程与模型调研、并行核查、推进补丁技术验证、初始化 Git，以及使用百炼本地 Key 和 5 元充值做真实小样。四模型各 40 条已完成，GLM 是候选而非已锁定主力；以下历史分析中的“仅授权迁移、尚未安装”是此前状态。

- [开源翻译执行器调研](research-projects.md)：已复用 AiNiee-Next CLI 完成真实试译；备选 GalTransl 通用 ForGal 工作流。配置、接口及格式兼容说明见[执行器实测](runner-setup.md)。
- [提示词、skill 与模型调研](research-style-models.md)：主要候选 DeepSeek V4-Pro、GLM-5.3-Flash、Qwen-MT-Plus、Index-Translate；DeepSeek V4.1-Flash 作成本对照，本地部署需要时考虑 Hy-MT2。推荐同资料盲评，尚无本游戏实测排名。
- [原文语体与用户文风约定](register-evidence.md)：日常对白易读，诗句、祈祷及名句适度保留古雅和戏剧感。
- [单 Key 接入方案](api-access.md)：百炼北京地域用户业务空间的一把 Key 已接通 DeepSeek Pro/Flash、智谱直供 GLM Flash 和 Qwen-MT。公开业务空间地址已保存；Index 预览未调用。
- [四模型真实试译结论](trial-results.md)：同一组 40 条真实资源共生成 160 条译文，批量 usage 保守折算约 0.121 元；全部输出核对源文与冻结响应，意义及中文审读问题已列明。当前优先考虑 DeepSeek Flash 作初稿，GLM 作局部文风对照，尚未执行全量。完整对照见 [comparison.md](../../../translation/trial-2026-10-09/comparison.md)。
- [真实试译输入](../../../translation/pilot/README.md)：187 条对白与 30 条资料，共 217 条；为 VNText 保留独立来源映射。4 项离线单元测试及 217 条来源/哈希检查通过。返场和互斥分支仍需拆清，不当作连续剧情。
- [补丁技术验证](technical-probe.md)：已安装离线样板，主菜单三个按钮中文渲染通过。后台静音自动导航设置页及 7 项 UI 集成断言通过，补充的 4 项失败分支回归通过。临时探针及游戏进程已清理，原游戏文件哈希未变；设置页像素排版、对白、资料界面和全量覆盖率尚未验收。

Git 已初始化。下载依赖、缓存和字体包不纳入 Git；未配置远端，也未推送。以下费用表保留此前估算，不代表本轮重新报价，最终以选定模型的小批量真实 usage 为准。

## 目标与用户偏好

用户最初比较现成工具与 AI 汉化补丁，希望工作量尽可能少并能开始玩中文游戏。已讨论过另一个 Adobe AIR 游戏 Detective Grimoire；它的 OCR 建议不能套用到本项目。

《Elsinore》是标准 Unity Mono 游戏，优先尝试游戏内文字替换。用户已明确接受借助 Codex 制作工具和补丁，并认为自己游玩时就能逐步校对，因此无需在全分支人工校验完之前等待。当前已安装 Sol 完整离线初稿；早期 API 小样作为历史证据保留。

## 本地发现

| 项目 | 结论 |
| --- | --- |
| 游戏位置 | `D:\SteamLibrary\steamapps\common\Elsinore` |
| 开发商 | Golden Glitch Studios |
| Unity 版本 | `2018.4.20f1`，读取 `globalgamemanagers` 得到 |
| 位数 | PE Machine `0x14c`，Windows x86 32 位 |
| 运行后端 | Mono，具有 `MonoBleedingEdge` 和可读的 Managed DLL |
| 文字框架 | 代码引用 TextMeshProUGUI；Managed 内有 `Unity.TextMeshPro.dll` |
| 剧情逻辑 | `Assembly-CSharp.dll` 有大量生成的剧情方法和英文字符串；`Elsinore.dll` 有自定义 Agakme 脚本相关类型 |
| 资源文字 | `resources.assets` 中有剧情脚本以及人物资料、线索、书信、知识等 JSON 类 TextAsset 载荷 |
| 外置数据 | `StreamingAssets` 主要是 Wwise 音频，未找到同参考项目一样的现成多语言 CSV |
| 官方语言 | 查阅 Steam 页面时仅有英语 |

主程序集与资源剧情脚本中的对白高度重复，所以两者不能累加当成译文量。程序集里存在编译后的对白，直接替换资源内源脚本未必覆盖全部运行路径。

## 已生成的成果

`analysis/analyze.py` 使用 Python 与 `pefile`，不加载或运行游戏代码：

- 根据名称、长度、有效 UTF-8 载荷和内容开头定位资源文本候选。
- 剧情脚本提取引号内自然语言，移除注释。
- 对资料资源去注释和尾随逗号后解析 JSON，只提取用于显示的字段。
- 读取 `Assembly-CSharp.dll` 的 .NET `#US` 字符串常量池，关联已提取的文本，把额外自然语言字符串列入待审核清单。
- 规范化空白并去重，保存原文及来源。

本次实际运行结果：

| 统计项 | 数值 |
| --- | ---: |
| 不同 TextAsset 载荷候选 | 56 |
| 主要待译候选条目 | 15,153 |
| 主要候选英文词 | 194,856 |
| 主要候选字符 | 1,017,168 |
| 对白候选条目 | 14,554 |
| 资料/界面候选条目 | 599 |
| 程序集原始字符串常量 | 20,566 |
| 程序集额外待审核条目 | 1,036 |
| 程序集额外候选英文词 | 12,706 |
| JSON 解析失败 | 0 |

以上属于静态候选统计：资源对象未用完整 Unity 类型解析器逐个验证；可能包含测试或未启用内容；未统计图片文字。类别可能交叉，额外程序集字符串含日志和程序提示，不应全部直接翻译。当前按约 19–22 万英文词估算全量翻译规模。

## 可行的补丁方向

先以 BepInEx 5 x86 Mono 加 XUnity.AutoTranslator 的手工翻译词表做少量样板。它支持 TextMeshPro，并能加载预制翻译字典；无需在游戏运行时逐条请求翻译服务。样板验证之后可以继续采用它，或用 Elsinore 专用的 BepInEx/Harmony 插件处理无法覆盖的路径。

补丁需要：

1. 一份可复现的提取与原文来源映射。
2. 按场景、说话人组织的翻译输入，角色称呼与术语表。
3. 对富文本标记、占位符、换行、格式和缺失译文的自动检查。
4. 预制译文的游戏内加载，保持存档及逻辑条件不受翻译影响。
5. 能显示所需中文字符的 TextMeshPro 字体资源和合适的换行、字号。
6. 用户游玩期间的反馈与快速词表更新。

不要把音效文件名、逻辑条件、方法名等标识当成正文翻译。先验证菜单、对白和人物/线索资料三种界面；游戏内实际显示和布局通过后才能称中文样板通过。

## 用户指定的参考项目

参考仓库：https://github.com/Aiden2014/PipistrelloHan

已经阅读 README、Plugin.cs、copy_translations.py、extract_unique_chinese_chars.py、add_char_to_main16.py 及项目配置。

其实现：

- 根据字符串 ID 和续行标记，把 ParaTranz 已译 CSV 的内容写入原始多语言 CSV 的 `ja_JP` 列。
- 从译文提取使用到的汉字，使用 Pillow 和中文像素字体渲染新的字体 PNG 图集。
- 当前 Plugin.cs 用 BepInEx 6 IL2CPP 与 Harmony：在 `Global.Init` 前扩展 `Global.fontCharRanges`；在 `Localization.ExtractFromCsv` 前读取插件的 `resources/strings.csv`；将 `SpriteManager.GetTexture` 的 `font/main16` 请求重定向到 `font/main16-han`。
- 工具链不包含 AI 翻译，它导入现成译文并制作显示补丁。

可借鉴“预制译文 + 小型加载插件 + 中文字体”的结构。不能直接照搬的部分包括游戏专用类名、CSV 日语语言槽、IL2CPP 插件接口和像素图集布局。本游戏是 Mono x86，文字来自脚本及程序集，字体使用 TextMeshPro。

源码与 README 有细节差异：README 描述的静态构造函数修补未见于当前 Plugin.cs，安装说明里的覆盖原资源流程也与当前 CSV/图片重定向方式不完全一致。复用时应以源码核实结果为准。

## Token 与成本估算

以下保留迁移时的历史价格与纯正文预估，不能当作本轮 Sol 实际 usage。真实完整任务用量见 sol-full.md。

一轮分批翻译，原文加提示词、编号和少量上下文，估计输入 40–70 万 token，译文及格式输出 20–40 万 token。额外思考、重试和校对会增加消耗；重复提示词缓存折扣未计入。

DeepSeek 官方当时人民币价（每百万 token，输入缓存未命中）：

| 模型 | 空闲输入 | 空闲输出 | 高峰输入 | 高峰输出 |
| --- | ---: | ---: | ---: | ---: |
| `deepseek-flash` / V4.1-Flash | ¥1 | ¥4 | ¥2 | ¥8 |
| `deepseek-v4-pro` / V4-Pro-0813 | ¥4.5 | ¥13.5 | ¥9 | ¥27 |

关闭思考时，一轮 Flash 估计空闲 ¥1.2–2.3，高峰 ¥2.4–4.6；Pro 估计空闲 ¥4.5–8.6，高峰 ¥9–17。模型默认启用思考，实际使用时需要显式选择模式。

GLM 此前使用阿里云百炼智谱原厂直供的人民币价格参考：GLM-5.3-Flash 输入 ¥0.8、输出 ¥2.8/百万；GLM-5.3 输入 ¥8、输出 ¥28/百万。仅按上面译文量计算，基线分别约 ¥0.9–1.7 和 ¥8.8–16.8。百炼当时列为仅思考模式，因此需要另外考虑思考 token。

Z.AI 官方国际站当时的 GLM-5.3-Flash 价格为输入 $0.15、输出 $0.50/百万，GLM-5.3 为输入 $1.4、输出 $4.4/百万。不能混淆不同平台的币种与接口价格。

来源：

- https://api-docs.deepseek.com/zh-cn/quick_start/pricing/
- https://api-docs.deepseek.com/quick_start/token_usage/
- https://api-docs.deepseek.com/guides/thinking_mode/
- https://docs.z.ai/guides/overview/pricing
- https://docs.bailian.console.aliyun.com/zh/model-studio/model-pricing

此费用估算已经被后续真实小样和 Sol 全文交付更新；不再等待模型、接口或 Key，不依据该表恢复测试。

## 工期口径与下一步

此前“可玩机翻需要数天、完整校对数周”的估计包含了更多人工验收，被用户指出过于保守。已修正为：先以几个小时内打通中文样板为目标；若拦截和字体兼容顺利，当天出可玩初版有可能，但目前未验证，不能保证。批量全译可以并发，用户玩到的内容再持续改进，无需先检查完所有分支。

当前维护事项：

1. 用户正常游玩中文初稿，遇到疑句按 F8 查看原文并反馈。
2. 根据真实反馈修订遗漏、含义和排版，保存精确修订记录并重新导出词表。
3. 测试继续使用后台静音模式，验收范围按证据表述；不恢复模型比较，不重复调用已完成批次。

完整初稿、F8 插件与字体已安装。最初迁移成果来自 C:\Users\71095\Documents\Elsinore-localization-analysis，历史研究和原始小样继续保留。

## 其他来源

- Steam 语言与游戏介绍：https://store.steampowered.com/app/512890/Elsinore/
- BepInEx：https://github.com/BepInEx/BepInEx
- XUnity.AutoTranslator：https://github.com/bbepis/XUnity.AutoTranslator
- XUnity 文档：https://github.com/bbepis/XUnity.AutoTranslator/blob/master/README.md

最新界面修复：用户截图暴露提取与动态消费漏项，已全审程序集93955处引用和资源51173处字段，正式词表16841条（原16228+613），保留正文raw，60格式别名复用。设置13值逐档+真实缓存48用例+19组件断言通过；已原目录安装与ZIP同步。MaxTextParserRecursion=64，需要重启加载配置；按路径隔离独立游戏副本，保存保护继续启用。入口docs/dev-tasks/localization/ui-audit.md、translation/supplemental/、analysis/ui-audit/；公开字体分发尚未完成。
