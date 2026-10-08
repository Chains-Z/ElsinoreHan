# 一把 API Key 的翻译接入方案

核查日期：2026-10-09。用户提供的一把北京业务空间 Key 已接通四个模型并完成真实试译，无需另申请 DeepSeek 或智谱 Key。原始凭证未打印、未写入公开配置或提交。

## 已提供的业务空间

用户已提供百炼北京业务空间并授权使用本地 `api-key.txt` 进行小样测试，充值 5 元。公开接入信息保存在 [translation/provider.json](../../../translation/provider.json)，不包含密钥；`.env.example` 已同步地址。

| 字段 | 用户提供值 |
| --- | --- |
| 说明 | AI 游戏翻译 |
| 业务空间名 | 默认业务空间 |
| 业务空间 ID | `ws-ffu0slce8mka9d9o` |
| API Host | `ws-ffu0slce8mka9d9o.cn-beijing.maas.aliyuncs.com` |
| OpenAI 兼容地址 | `https://ws-ffu0slce8mka9d9o.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` |
| DashScope 地址 | `https://ws-ffu0slce8mka9d9o.cn-beijing.maas.aliyuncs.com/api/v1` |

本轮接入统一使用业务空间专属地址；密钥只在运行时从被 Git 忽略的文件读取，不打印或写进公开配置。先核对模型权限，再执行受 5 元总预算约束的小批量试译；这些地址是用户现场值，优先于下文通用域名示例。

## 建议方案

优先使用 [阿里云百炼](https://bailian.console.aliyun.com/)，选择 **华北2（北京）**、同一个业务空间的常规按量模型服务 API Key。主要试译覆盖 DeepSeek、智谱原厂直供 GLM 和 Qwen-MT，不需要分别去 DeepSeek、智谱申请账号和密钥。

[官方 Key 说明](https://help.aliyun.com/zh/model-studio/get-api-key) 明确同一业务空间无需为不同模型创建不同 Key；地域之间的 Key 与接入地址不能混用。[智谱直供说明](https://help.aliyun.com/zh/model-studio/glm-zhipu) 限定北京地域，且要求在百炼内开通模型服务并确认授权。因此“一把 Key”仍可能需要在同一控制台点选服务开通，不等于所有模型默认已获权限。

| 试译对象 | 百炼模型名 | 已核实依据 |
| --- | --- | --- |
| DeepSeek V4-Pro 固定版本 | `deepseek-v4-pro-0813` | [官方模型卡](https://help.aliyun.com/zh/model-studio/deepseek-v4-pro) |
| DeepSeek V4.1-Flash | `deepseek-v4.1-flash` | [官方 API](https://help.aliyun.com/zh/model-studio/deepseek-api) |
| GLM-5.3-Flash，智谱直供 | `ZHIPU/GLM-5.3-Flash` | [官方模型卡](https://help.aliyun.com/zh/model-studio/glm-5-3-flash-by-zhipu) |
| Qwen-MT-Plus，专用翻译 | `qwen-mt-plus` | [官方模型卡](https://help.aliyun.com/zh/model-studio/qwen-mt-plus) |
| GLM-5.3，可选旗舰对照 | `ZHIPU/GLM-5.3` | [官方直供 API](https://help.aliyun.com/zh/model-studio/glm-zhipu) |

用户只需要完成一次平台注册/服务开通、创建一把北京地域 Key，以及 GLM 的同平台服务开通。若控制台要求实名认证，应按 [官方首次调用指南](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen) 完成。先小批量试译并记录真实用量，再决定全量模型和费用，不先买长期套餐。

## 其他平台与可选模型

- [OpenRouter 官方模型目录](https://openrouter.ai/api/v1/models)：核实到当前 DeepSeek 与 GLM，但本次目录未检索到 `qwen-mt`，因此不作为这组完整对比的首选；通用 Qwen 不能代替 Qwen-MT 专用翻译模型。
- [硅基流动模型中心](https://www.siliconflow.cn/models)：核实到 DeepSeek 与 GLM，但当前公开页未检索到 Qwen-MT。这是本次检索结果，不证明平台绝对没有其他入口。
- [Index-Translate 官方项目](https://github.com/bilibili/Index-Translate)：当前提供公开免费预览端点，官方示例无需申请单独密钥，可作为额外小样对照。它不通过百炼 Key；若预览不可用则暂时跳过，不要求用户另申请账号。
- Hy-MT2 保留本地部署候选，不作为本次云端试译需要用户申请的凭证。

## 本地配置与接入边界

密钥保存在本机即可，不发送到聊天。项目提供 [.env.example](../../../.env.example) 作为字段示例；`.env` 被 Git 忽略，示例只包含空密钥和公开模型名。本轮实际从 `translation/provider.json` 读取公开配置，从 `api-key.txt` 临时注入凭证，四候选已调用成功。

百炼优先推荐业务空间专属域名：`https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`。官方仍支持 `https://dashscope.aliyuncs.com/compatible-mode/v1`；当前模板和实际调用已使用上文业务空间专属地址。

同一 Key 不代表请求参数完全相同：

- 百炼 DeepSeek 使用 `enable_thinking`，与 DeepSeek 原厂的 `thinking.type` 参数区别见 [百炼 DeepSeek API](https://help.aliyun.com/zh/model-studio/deepseek-api)。
- 智谱直供 GLM 的 5.3 系列只支持思考模式，需要保留思考预算并分别记录最终译文和 reasoning 用量。
- Qwen-MT 只接收单条 user 消息，按 [翻译 API](https://help.aliyun.com/zh/model-studio/machine-translation/) 传入 `translation_options`。不能把通用聊天模型的 system/user JSON 提示原封不动发送给它。
- 模型卡中的“批量推理不支持”指平台异步 Batch 功能；本项目仍可由现成执行器分块、限速、多次普通请求处理全量文本。

账户权限、连通性及 40 条批量输出已真实验证，结果见[四模型试译结论](trial-results.md)。按返回 usage 折算费用，不具备账户实际账单查询结果。汉化补丁的离线词表与中文显示验证不需要 API Key，只有真实模型试译和批量翻译才需要。

## Flash 与 FlashX

用户已在百炼开通智谱直供服务，普通 `ZHIPU/GLM-5.3-Flash` 已调用成功。FlashX 不是本轮新增付费候选。

| 项目 | Flash | FlashX |
| --- | ---: | ---: |
| 输入原价，元/百万 token | 0.8 | 2 |
| 输出原价，元/百万 token | 2.8 | 7 |
| 产品定位 | 低成本通用模型 | 高速模型，官方宣传 200 token/s |

来源：[Flash 官方模型卡](https://help.aliyun.com/zh/model-studio/glm-5-3-flash-by-zhipu)、[FlashX 官方模型卡](https://help.aliyun.com/zh/model-studio/glm-5-3-flashx-by-zhipu)，2026-10-09 核查。未命中缓存时 FlashX 输入输出均为普通 Flash 的 2.5 倍价格。官方卡没有提供本游戏翻译质量对比，也不能据此认定两者权重完全相同；离线预译优先质量与费用，因此本轮先使用普通 Flash。
