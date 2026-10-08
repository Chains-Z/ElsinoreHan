# 汉化任务分析与交接

## 2026-10-09 当前进展

本轮用户已授权翻译流程与模型调研、并行核查、推进补丁技术验证和初始化 Git。模型尚未选定，GLM 只是候选；以下历史分析中的“仅授权迁移、尚未安装”是此前状态。

- [开源翻译执行器调研](research-projects.md)：建议先复用 AiNiee-Next；备选 GalTransl 通用 ForGal 工作流。已核实说话人输入、缓存、字典和输出元数据局限，没有运行上游工具或调用模型。
- [提示词、skill 与模型调研](research-style-models.md)：主要候选 DeepSeek V4-Pro、GLM-5.3-Flash、Qwen-MT-Plus、Index-Translate；DeepSeek V4.1-Flash 作成本对照，本地部署需要时考虑 Hy-MT2。推荐同资料盲评，尚无本游戏实测排名。
- [原文语体与用户文风约定](register-evidence.md)：日常对白易读，诗句、祈祷及名句适度保留古雅和戏剧感。
- [真实试译输入](../../../translation/pilot/README.md)：187 条对白与 30 条资料，共 217 条；为 VNText 保留独立来源映射。4 项离线单元测试及 217 条来源/哈希检查通过。返场和互斥分支仍需拆清，不当作连续剧情。
- [补丁技术验证](technical-probe.md)：已安装离线样板，主菜单三个按钮中文渲染通过。后台静音自动导航设置页及 7 项 UI 集成断言通过，补充的 4 项失败分支回归通过。临时探针及游戏进程已清理，原游戏文件哈希未变；设置页像素排版、对白、资料界面和全量覆盖率尚未验收。

Git 已初始化。下载依赖、缓存和字体包不纳入 Git；未配置远端，也未推送。以下费用表保留此前估算，不代表本轮重新报价，最终以选定模型的小批量真实 usage 为准。

## 目标与用户偏好

用户最初比较现成工具与 AI 汉化补丁，希望工作量尽可能少并能开始玩中文游戏。已讨论过另一个 Adobe AIR 游戏 Detective Grimoire；它的 OCR 建议不能套用到本项目。

《Elsinore》是标准 Unity Mono 游戏，优先尝试游戏内文字替换。用户已明确接受借助 Codex 制作工具和补丁，并认为自己游玩时就能逐步校对，因此无需在全分支人工校验完之前等待。当前只授权研究与成果迁移，尚未选定翻译 API 或要求实际安装补丁。

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

核价日期：2026-10-09。没有实际调用模型；以下是预估，不能当作真实 usage。

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

实际预算以选定模型后的小批量试译 usage 外推更可靠。用户尚未指定模型、服务渠道、API Key 或预算。

## 工期口径与下一步

此前“可玩机翻需要数天、完整校对数周”的估计包含了更多人工验收，被用户指出过于保守。已修正为：先以几个小时内打通中文样板为目标；若拦截和字体兼容顺利，当天出可玩初版有可能，但目前未验证，不能保证。批量全译可以并发，用户玩到的内容再持续改进，无需先检查完所有分支。

接手后的首要工作：

1. 确认本目录与游戏现场状态，检查是否已有用户新增文件或补丁。
2. 根据用户后续指令，验证中文显示样板；当前的未知是文字拦截覆盖率及字体兼容性。
3. 完善提取的稳定 ID、场景与说话人信息，审核程序集额外文字，避免混入程序逻辑。
4. 选定模型与 API，先小批量翻译并核对 usage，再执行全量批处理。
5. 用机器检查和实际游戏显示确认初版，建立随游玩更新译文的办法。

没有安装插件，没有更改游戏文件，没有真实翻译调用，没有游戏内验收。迁移前四个分析成果原位于 `C:\Users\71095\Documents\Elsinore-localization-analysis`，现归本项目维护。

## 其他来源

- Steam 语言与游戏介绍：https://store.steampowered.com/app/512890/Elsinore/
- BepInEx：https://github.com/BepInEx/BepInEx
- XUnity.AutoTranslator：https://github.com/bbepis/XUnity.AutoTranslator
- XUnity 文档：https://github.com/bbepis/XUnity.AutoTranslator/blob/master/README.md
