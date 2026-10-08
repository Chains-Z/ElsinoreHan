# AI 游戏文本翻译工具调研

核查日期：2026-10-09。范围是已提取的英语剧情、资料和界面文本，离线批量译成简体中文；游戏加载与字体另行验证。本次仅查阅公开文档和源码，没有把游戏原文发送到外部模型，也没有调用翻译 API。

## 结论

优先复用 **AiNiee-Next 的通用 API 翻译执行器**，以 VNText JSON 保留说话人，在项目侧保留稳定 ID、原文哈希和格式验收。用户尚未决定模型，GLM 是可接入候选，同一工作流也能比较其他模型。若更看重分场景台词工作台、逐句校对和结构化对齐，可以采用 **GalTransl 的 ForGal-json 后端**。两者已经覆盖分批、上下文、术语和恢复，没必要重新实现完整翻译框架。

这是基于公开代码的选型建议，不是本项目实测质量排名。工具支持 GLM 接口也不等于译文已经自然；文风、人物关系、固定译名及试译验收仍需配置。

## 候选比较

| 项目 | 已核实能力 | 对本项目的作用 | 适配代价 |
| --- | --- | --- | --- |
| [AiNiee](https://github.com/NEKOparapa/AiNiee) | 游戏导出格式、通用语言、角色/背景/风格配置、术语、润色，AGPL-3.0 | 适合希望图形界面查看和调整译文的用户 | 需转成支持的游戏 JSON，不直接读取 Unity 原文结构 |
| [AiNiee-Next](https://github.com/ShadowLoveElysia/AiNiee-Next) | AiNiee 核心的 CLI/TUI 分支，缓存恢复、队列、API 配置，AGPL-3.0 | 适合 Codex 管理不同模型的 API 跑批，用户随玩随校对 | VNText 输出丢弃额外 ID；需项目映射和结果校验 |
| [GalTransl](https://github.com/GalTransl/GalTransl) | 台词姓名、字典、实时缓存、断点续翻、问题列表，GPL-3.0 | 适合场景台词与资料分别组织，保留相邻语境 | 必须使用通用 ForGal 模板并替换默认日系文风规范 |

AiNiee 的定位和格式来自其 [README](https://github.com/NEKOparapa/AiNiee/blob/main/README.md)；Next 的批处理能力来自其 [README](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/main/README.md)；GalTransl 的台词工作流来自其 [README](https://github.com/GalTransl/GalTransl/blob/main/README.md)。这些都是工具作者声明，速度宣传和“提高质量”没有在《Elsinore》验证。

许可证已核对上游 [AiNiee LICENSE](https://github.com/NEKOparapa/AiNiee/blob/main/LICENSE)、[AiNiee-Next LICENSE](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/LICENSE) 和 [GalTransl LICENSE](https://github.com/GalTransl/GalTransl/blob/4dfcce507420ba29e24b630de9f724c2b6873678/LICENSE)。建议把上游作为独立工具调用，保留版本和出处；若复制或改造代码后分发，再按具体许可证处理。

## AiNiee-Next：GLM 接口与输入契约

核查版本：`b0883c9f806984571d8f9fe8c4345425d1e6fe83`。

不是仅凭“OpenAI 兼容”推测：其 [平台预设](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/Resource/platforms/preset.json) 已有 `zhipu`，地址为 `https://open.bigmodel.cn/api/paas/v4`，请求格式 `OpenAI`，`auto_complete=false`；另有自定义接口。预设模型仍包含旧名称，实际应填用户选定渠道当前可用的模型，不能把预设列表当最新模型推荐。RPM/TPM 必须按实际账号限额调整。

最直接的剧情输入是 `Vnt` 类型，JSON 数组中的对象使用 `message` 和可选 `name`/`names`。这是上游 [VntReader](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Domain/FileReader/VntReader.py) 的真实契约。Reader 把单个说话人转换为 `[name]message`，因此说话人确实进入翻译文本；多人姓名也有对应处理。`Vnt` 是 [实际类型枚举](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Infrastructure/Cache/CacheProject.py)，不是任意格式名称。

不要把稳定 ID 只塞进 VNText 对象：Reader 只保存姓名信息，[VntWriter](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Domain/FileOutputer/VntWriter.py) 重建输出时仅写 `message`、`name` 或 `names`，额外 `id` 和来源字段不会保留。Writer 从译文开头的方括号提取姓名，提取失败会回退；结果导入前须检查姓名残留和正文边界。

另一交换格式是 ParaTranz 的 `key`、`original`、`translation`、`context`、`stage`。初始 `stage=0` 表示未译；其他 stage 会被视为已译。该规则来自 [ParatranzReader](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Domain/FileReader/ParatranzReader.py)。`context` 在 Reader 中存为元数据，尚未确认能逐条随请求传给模型，不能仅靠它提供说话人。

[ParatranzWriter](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Domain/FileOutputer/ParatranzWriter.py) 保留 `key` 和 `context`，但只输出已译或已润色条目，不写 `stage`，未译条目被丢弃。因此输出必须按 `key` 合并到原始清单；不能直接覆盖主清单，也不能假定输出条数一定等于输入。

其 [PromptBuilder](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Domain/PromptBuilder/PromptBuilder.py) 支持术语、禁翻项、角色信息、世界观、措辞风格、译例、前文和历史译文参考。`writing_style` 和译例用于控制中文口吻，姓名/地名放术语表；无需把全部角色资料复制到每条文本。原版 [Inspect 文档](https://github.com/NEKOparapa/AiNiee/wiki/检查（Inspect）) 主要介绍残留语言检测，不能替代游戏标签、变量和占位符的严格验收。

## GalTransl：适合借鉴的剧情工作流

核查版本：`4dfcce507420ba29e24b630de9f724c2b6873678`。

[默认 JSON 插件](https://github.com/GalTransl/GalTransl/blob/4dfcce507420ba29e24b630de9f724c2b6873678/plugins/file_galtransl_json/file_galtransl_json.py) 读取 `message` 和可选 `name` 对象数组；`output_with_src` 可保留原文副本。配置中的 OpenAI-Compatible 允许填写 endpoint/model。[样例配置](https://github.com/GalTransl/GalTransl/blob/4dfcce507420ba29e24b630de9f724c2b6873678/sampleProject/config.inc.yaml) 已提供批量行数、前文数、多轮上下文、分片重叠、缓存保存步数、重试上限和失败句重翻。

英语原文应选择通用 ForGal 模板。[提示词源码](https://github.com/GalTransl/GalTransl/blob/4dfcce507420ba29e24b630de9f724c2b6873678/GalTransl/Backend/Prompts.py) 的 ForGal 明确允许任意源语言译到目标语言，并用姓名、历史译文、术语和固定 ID 对齐结果。旧 DeepSeek/Sakura/GalTransl 专用模型提示仍写日文到中文，不应直接用于本游戏。样例没有 `sourceLanguage=en` 配置项，不能杜撰该参数。

GLM endpoint 的最终拼接需小批量实测；文档说明完整 `/chat/completions` 地址不会自动补 `/v1`，而智谱原厂使用 `/api/paas/v4`。选定渠道后必须核对实际请求路径，不能盲目套 OpenAI 根地址。

默认 [Basic.md](https://github.com/GalTransl/GalTransl/blob/4dfcce507420ba29e24b630de9f724c2b6873678/translation_guidelines/Basic.md) 面向 ACGN，含删除日文促音、按主角第一人称补旁白主客体的规则。对《Elsinore》不合适，必须改用英文剧情规范，保留原有叙事视角、时代氛围和人物差异。

[常规问题插件](https://github.com/GalTransl/GalTransl/blob/4dfcce507420ba29e24b630de9f724c2b6873678/plugins/problem_common/problem_common.yaml) 涵盖日文残留、标点、换行和字典等检测；英中原文需要补适用的英语残留及本游戏占位符检查。插件通过不代表没有错译。

## Skill 与 Translator++ 的边界

AiNiee-Next 确实附有 [SKILL.md](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/SKILL.md)，定位是外部 Agent/MCP 协作规约，强调受控原文读取、批次领取和配置边界。它不是一份直接交给 GLM 的中文文风提示词。当前仅调研，没有安装或激活该技能。

AiNiee 上游还推荐 [ainiee-translate-skill](https://github.com/xuanji86/ainiee-translate-skill)，它将词汇表、分批、润色、验证等流程拆成命令，适合研究流程组织；默认描述由 Claude Code 充当翻译引擎，不等于 GLM API 跑批执行器。译文由谁生成、使用哪个计费接口，必须明确。

Translator++ 是导出与编辑游戏翻译工程的一条路线；AiNiee 和 GalTransl 都能处理其导出格式。对本项目已有提取清单，额外引入完整提取工具并无已证实收益。这里推荐的是现成翻译执行器，不声称 Translator++ 能直接处理本游戏的资源和编译对白，也不把它当 GLM 自然译文保证。

## 本项目建议的复用顺序

以下是结合本地清单特点的实施建议，不是上游规定：

1. 从真实资源按场景和原始顺序选取约 150 条，包括连续对白、独白、界面和资料。先得到少量可比较的结果，确认文风后全译。
2. 同时保留主清单和 `manifest`：稳定 ID、文件/行号、真实原文、说话人、分类、原文哈希、标签及占位符。VNText 文件只作为翻译输入，不能成为唯一事实来源。
3. 用 AiNiee-Next 的传统 API 模式先跑样本，显式设置英语到简体中文；用相同样本和约束比较候选模型。初始每批约 10–20 条、少量前文、低并发；连续场景独立文件，别把不相关分支拼成一段对话。上游 [快速教程](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/main/Docs/README_QUICK_START_EN.md) 也建议先小文件确认接口、提示、术语与输出，再增加并发。
4. 在已有基础提示上加入本作风格：对白自然、按人物身份保持口吻；资料克制清楚；保留幽默、讽刺、迟疑和含混；不额外解释剧情，不擅自升格为文言或网络梗。固定姓名与称谓单独锁定，提供少量来自真实原文且用户认可的译例。
5. 批量后对每条验证 ID/条数、非空译文、姓名边界、占位符数量及内容、富文本标签、强制换行、数字与逻辑标记。失败只回炉相关批次；缓存与最终验收状态分开管理，避免“API 成功”被当作“译文合格”。
6. 对生硬、意义不明或屏幕过长条目做局部复核/润色，同时提供英语原文与角色背景，避免只看中文后自由改写。上游 [质量教程](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/main/Docs/TRANSLATION_WORKFLOW_GUIDE.md) 也将翻译规则、术语、背景和润色分开，并说明润色不能救回严重错译。
7. 将验收过的结果回填稳定 ID，再生成补丁词表。真实 LLM 翻译验证与游戏消费冻结译文的验证分开，不重复调用模型来测试字体或加载。

当前仍待实测：候选模型与渠道、请求参数兼容性、真实中文读感、实际 usage、缓存恢复、输出到补丁词表的完整往返。没有必要因这些未知重新造整个翻译框架。
