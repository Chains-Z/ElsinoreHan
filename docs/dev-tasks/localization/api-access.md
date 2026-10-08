# 一把 API Key 的翻译接入方案

核查日期：2026-10-09。用户希望减少平台注册与密钥申请，优先一把 Key 覆盖模型对比；目前没有申请密钥、读取凭证或调用翻译模型。

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

密钥保存在本机即可，不发送到聊天。项目提供 [.env.example](../../../.env.example) 作为字段示例；复制为项目根的 `.env` 后填写 `DASHSCOPE_API_KEY`。`.env` 已被 Git 忽略，示例只包含空密钥和公开模型名。该文件是本地凭证配置约定，现成执行器的接入配置仍需在实际试译时完成，不能声称已经调用成功。

百炼优先推荐业务空间专属域名：`https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`。官方仍支持 `https://dashscope.aliyuncs.com/compatible-mode/v1`，模板先使用此地址，避免要求用户额外手工拼接；实际工具配置由 agent 处理。

同一 Key 不代表请求参数完全相同：

- 百炼 DeepSeek 使用 `enable_thinking`，与 DeepSeek 原厂的 `thinking.type` 参数区别见 [百炼 DeepSeek API](https://help.aliyun.com/zh/model-studio/deepseek-api)。
- 智谱直供 GLM 的 5.3 系列只支持思考模式，需要保留思考预算并分别记录最终译文和 reasoning 用量。
- Qwen-MT 只接收单条 user 消息，按 [翻译 API](https://help.aliyun.com/zh/model-studio/machine-translation/) 传入 `translation_options`。不能把通用聊天模型的 system/user JSON 提示原封不动发送给它。
- 模型卡中的“批量推理不支持”指平台异步 Batch 功能；本项目仍可由现成执行器分块、限速、多次普通请求处理全量文本。

已核实接口文档与模型目录，尚未验证用户账户授权、连通性、输出格式、中文质量和真实计费。汉化补丁的离线词表与中文显示验证不需要 API Key，只有真实模型试译和批量翻译才需要。
