# 扩大样本的现成执行器配置与 Qwen 原生适配

## 接口

保留 AiNiee-Next commit `b0883c9f806984571d8f9fe8c4345425d1e6fe83` 的 Reader、分批调度、请求器和 Writer。此次增加独立试验目录，默认仍是原来的 `translation/trial-2026-10-09/`，没有重译或修改已完成的 40 条。

以下四个入口接受 `--trial-dir <目录>`：

- `tools/translation/prepare_trial_rules.py`：真实上下文和术语转上游规则。
- `tools/translation/run_existing_trial.py`：配置并调用现成翻译 CLI。
- `tools/translation/recover_trial.py`：离线从冻结真实响应严格恢复。
- `tools/translation/build_trial_report.py`：离线来源、响应和格式核对及对照表。

执行器还接受 `--budget-cny`、`--max-posts`、`--lines`、`--max-output-tokens`。命令行显式参数优先，其次读取试验目录内 `trial-config.json`，否则保留旧默认值（4.75 元、24 次、15 行、4096 输出 token）。新轮必须配置独立的 1 元预算，例如：

```json
{
  "budget_cny": 1.0,
  "max_posts": 140,
  "lines": 20,
  "max_output_tokens": 4096
}
```

每轮的模型共用该目录内 `api-ledger.jsonl`，逐个模型、逐个批次顺序运行；跨进程并行付费仍不支持。已有候选输出默认拒绝重复付费；`--resume-failed` 只继续失败或尚未跑的批次，全部预期批次通过后仍拒绝重跑。试验目录和本轮参数记录在运行配置中，输出、账本和恢复证据均按目录隔离。

```powershell
python tools/translation/prepare_trial_rules.py --trial-dir translation/trial-expanded-2026-10-09
python tools/translation/run_existing_trial.py --trial-dir translation/trial-expanded-2026-10-09 --candidate qwen_mt
```

首次 Qwen 真实批次可加 `--stop-after-batches 1`：只新执行一批后记录运行状态，供核对冻结响应和解析结果。之后带 `--resume-failed` 继续，其余已通过批次跳过且保留全部旧批次记录。停止数只能是正整数；部分批次通过不等于整个候选完成。请求次数不是样本行数：上游拆批后一次输入文件可能发出多次请求，26 个输入文件、四候选至少 104 次，140 次上限为格式拆批留下余量，金额硬闸仍是 1 元。

## Qwen-MT 原生参数

旧适配把 system 和 user 拼成一段待译文，导致模型翻译背景和提示。新适配只取最后一条 user 消息的最后一个完整源文 `textarea`；剥去工具包装后，发送完整编号源行，保留姓名元数据。缺明确源块、重复编号、夹杂解释或空行在网络发送前拒绝，不从提示正文猜测源文。

术语从本批上游规则中的 `prompt_dictionary_data` 转为官方 `translation_options.terms` 的 `source` / `target`。清楚自然的简体中文、保留原有适度戏剧语气、不得添写事实及严格保留编号、姓名、标签等要求走 `translation_options.domains`。官方说明 domains 当前只支持英文，故新增上下文需通过 `context.json` 的 `batches.<batch_id>.qwen_mt_domains` 提供英文摘要；制备规则时原样复制。不会把中文背景直接混入原生 domains。若缺该字段，仅有通用英文游戏文风要求，该候选缺少特定场景背景，质量对比时必须说明这个限制。

官方支持自定义提示与原生参数共用，但推荐优先原生 `translation_options`；此处没有把整段上游提示当自定义待译文。[Qwen-MT 使用说明](https://help.aliyun.com/zh/model-studio/machine-translation)，[API 参数](https://help.aliyun.com/zh/model-studio/qwen-mt-api)。

输出侧只在模型返回完整、唯一且顺序一致的编号行时，离线补回 AiNiee 所需 `textarea`。原响应在账本保持原样，包装动作单独审计；不改任何译句。少编号、乱序、解释或截断均不自动修复。冻结恢复通过请求源行与真实输入精确匹配，并验证译文编号集合及顺序；不根据语义或位置猜测缺失译文。

## 验证与局限

2026-10-09，本次执行器修改完成 23 项项目离线回归和 20 项上游适配回归。其中新增 Qwen 原生集成覆盖真实 Reader → Executor → HTTPX 离线传输 → 可逆包装 → Writer；使用实际本地游戏来源片段，固定译文响应只用于验证消费者与格式链，不能称真实模型 E2E。另有完整编号、缺行、重复编号、无源块、中文 domains 拒绝、原生参数传递、冻结恢复和受控暂停合并状态回归。

本执行器修改未读取实际 API Key、没有新发付费请求。真实 Qwen 首批仍需主 agent 使用本轮真实数据调用后验收；不能由离线传输证明模型会遵守编号与行边界。后续真实结果不得覆写成更顺口的句子掩盖原始输出。

费用闸按真实 usage 释放已知预留，超时/缺统计继续保留。GLM 仍对可能的思考 token 额外保守预留 131072，因此单次预留约 0.38 元；应较早测试 GLM，避免其他候选累计用量压缩余额后提前拒绝。该行为不允许为了跑完而越过本轮 1 元授权上限。
