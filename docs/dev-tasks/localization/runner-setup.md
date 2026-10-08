# 现成翻译执行器的本地准备

核查日期：2026-10-09。固定上游 [AiNiee-Next](https://github.com/ShadowLoveElysia/AiNiee-Next/tree/b0883c9f806984571d8f9fe8c4345425d1e6fe83)，版本 `b0883c9f806984571d8f9fe8c4345425d1e6fe83`。此记录覆盖执行器准备和离线配置验证；没有读取 `api-key.txt`，没有发起模型调用或真实试译。

## 已准备的本地环境

- 上游源码：`runtime/vendor/AiNiee-Next/`，通过固定提交 ZIP 下载。该目录被 Git 忽略，许可证保留上游 AGPL-3.0。
- 隔离 Python：`runtime/vendor/AiNiee-Next/.venv/Scripts/python.exe`，版本 3.12.10；没有改默认 Python。
- 安装文本输入、批量执行、HTTP 与 SDK 所需依赖，已通过 `TaskExecutor`、`FileReader`、`FileOutputer` 导入。上游 PDF/OCR/BabelDOC 路径没有安装或验收。
- 上游 Reader 仍强制导入 MediaPipe，即使只读 VNText 也需要该依赖。安装了兼容其 `LanguageDetector` 的 `mediapipe==0.10.21`、`protobuf==4.25.7`，依赖解析落到 NumPy 1.26.4。该环境是实际通过导入的文本执行环境，**不是完整 pyproject 的所有依赖组合**；上游完整 pyproject 声明 NumPy ≥2。已安装精确版本记录在忽略目录 `deps-text-runtime.freeze.txt`。
- 未启动交互 TUI、WebUI、可见窗口或游戏；任务通知在试译模板中禁用。

## 命令和安全注入

先准备不含密钥的独立 profile，模型名称必须由百炼实际核实结果替换：

```powershell
$runnerPython = 'runtime/vendor/AiNiee-Next/.venv/Scripts/python.exe'
& $runnerPython tools/translation/upstream-runner/prepare_config.py `
  --base-url 'https://ws-ffu0slce8mka9d9o.cn-beijing.maas.aliyuncs.com/compatible-mode/v1' `
  --model '<verified-model-id>' `
  --prompt '<system-prompt.txt>' `
  --style '<writing-style.txt>' `
  --rules '<rules-profile.json>'
```

`--prompt`、`--style`、`--rules` 都可省略。提示省略时用上游 `common_system_zh.txt`，正式试译应传入本作提示并保持上游 `<textarea>`、逐行编号输出契约。配置脚本只写被忽略的上游 `Resource/config.json`、`profiles/elsinore-pilot.json` 和 `rules_profiles/elsinore-pilot.json`。不接收 Key 参数，平台 Key 留空。

运行由上游完整执行分批、上下文、重试和缓存。项目启动器只做百炼参数适配：

```powershell
& $runnerPython tools/translation/upstream-runner/launch.py translate '<pilot-input.json>' `
  --execution-mode default_api --type Vnt --source english --target chinese_simplified `
  --profile elsinore-pilot --rules-profile elsinore-pilot --output '<output-dir>' `
  --threads 1 --retry 0 --rounds 1 --timeout 90 --lines 15 --pre-lines 0 --failover off --yes
```

实际密钥应由父进程在创建 subprocess 时通过 `env["AINIEE_WEB_TASK_API_KEY"]` 注入，不写命令行 `--api-key`，不打印环境。该变量由上游 `ainiee_cli.py::_consume_web_task_api_key` 在运行时消费并从环境删除；`CommandModeRunner` 使用临时 `runtime_config_overrides`，不把临时 Key 写进 profile。不要把真实 Key 填到保存的上游 JSON。

`--resume` 支持续跑，比较不同模型应使用独立输入副本、输出目录和缓存，防止共用旧译文；费用审计账本则统一使用同一文件，实现全模型总预算。首次仅给少量文本，不能把全部 217 条输入当作已经验收可全跑。

启动器先把常用 input、`--output/-o`、workflow/queue 文件路径转为绝对路径，然后把工作目录切到固定上游根目录。上游 `TextProcessor` 和基础提示加载器依赖相对 `Resource/` 路径，不能继续以项目根目录作为上游执行 cwd。复杂参数排列或内联 `--output=...` 形式建议直接给绝对路径。

语言字段与 CLI 均可使用 `source_language=english` / `--source english`、`target_language=chinese_simplified` / `--target chinese_simplified`。`TranslatorUtil` 明确将这两个内部名称映射为英语和简体中文；`TaskContract` 原样传递字符串，不做隐式文种转换。上游 `Resource/platforms/preset.json` 默认开启 `response_conversion_toggle=true` 且 `opencc_preset=s2twp.json`，这会在翻译后转繁体，与语言参数无关。模板显式覆盖为 `response_conversion_toggle=false`、`opencc_preset=t2s.json`，保持模型简体输出并使备用配置方向也为简体。

## 平台参数与百炼兼容

`custom.api_url` 保存完整 `.../compatible-mode/v1`，`auto_complete=true`。HTTPX 请求器最终追加 `/chat/completions`，不是 DashScope 原生文本生成路径。`custom.model`、CLI `--model` 都能设置模型。输出限制 `custom.max_output_tokens` 确实传入 `max_tokens`。

百炼思考开关使用 `custom.extra_body={"enable_thinking":false}`，HTTPX 模式直接合并为请求体顶层字段。DeepSeek 初始关闭思考；`ZHIPU/GLM-5.3-Flash` 经主流程连通实测需要开启思考，使用 `prepare_config.py --thinking true` 设置 `extra_body={"enable_thinking":true,"reasoning_effort":"low"}`。顶层 `think_switch=false` 保持由百炼专用 extra 参数控制，不交给上游原厂推断。初始配置禁用流式，降低接口差异。

固定上游会按 `deepseek` 模型名前缀推断原厂协议并自动追加 `thinking={"type":"disabled"}`。这一推断不适用于百炼的 `enable_thinking` 契约。`bailian_compat.py` 仅对百炼业务空间主机或官方 DashScope 主机关闭原厂推断，保持真实 DeepSeek 原厂地址的原有行为；同步与异步请求器同时适配。不改上游源码，不增加翻译调度。

HTTPX 模式已离线验证；OpenAI SDK 模式 `extra_body` 的包装差异及不同模型接受哪些附加字段必须真实小样核实。该准备不意味着 GLM 或 DeepSeek 已开通。Qwen-MT 的专用参数桥接见下节，离线通过不等于真实接口与翻译质量通过。

## 输出、上下文和规则配置

输入 `Vnt` 是 `[{"name":"Ophelia","message":"英文原文"}]`。运行时姓名以 `[Ophelia]` 进入待译文本，输出仍为 JSON 对象数组，只有 `message`、`name` 或 `names`；额外稳定 ID 会丢弃，必须在项目 manifest 中另存并核对数量、顺序和姓名边界。

提示词接口不是要求模型返回 JSON：上游基础提示要求 `<textarea>` 内逐行编号，执行器解析响应后由 `VntWriter` 生成 JSON。自定义系统提示不能擅自改成 JSON 输出，除非同时选择上游支持的结构化模式并验证解析。

`pre_line_counts` / `--pre-lines` 控制上文行数。样本包含返场和条件分支，默认 0，按实际可确认连续场景才设 2–3。历史译文参考通过上游 `translation_memory_switch` 与既有译文检索，首次比较关闭，避免模型交叉污染；`writing_style_history` 和 `world_building_history` 是配置历史，不能误认为聊天历史。无需自己实现历史缓存。

可传入 `--rules` JSON：

```json
{
  "prompt_dictionary_switch": true,
  "prompt_dictionary_data": [
    {"src": "Ophelia", "dst": "奥菲莉娅", "info": "角色名，译名待统一确认"}
  ],
  "characterization_switch": true,
  "characterization_data": [
    {
      "original_name": "Ophelia",
      "translated_name": "奥菲莉娅",
      "speech_style": "遵循原句态度，清楚易读，普通对白不人为古化"
    }
  ],
  "world_building_switch": true,
  "world_building_content": "作品改编自《哈姆雷特》，只保留原文已有的戏剧感，不补写剧情背景。"
}
```

`writing_style_switch=true`、`writing_style_content` 可由 `--style` 写入。`translation_example_switch` 和 `translation_example_data` 支持译例，需使用来自真实原文且通过确认的例子。上游 [PromptBuilder](https://github.com/ShadowLoveElysia/AiNiee-Next/blob/b0883c9f806984571d8f9fe8c4345425d1e6fe83/ModuleFolders/Domain/PromptBuilder/PromptBuilder.py) 会按命中选术语与角色；`character_recall_switch=false` 保持简单关键词匹配。

## 成本与限制

没找到上游传统 API 执行器的人民币预算硬闸。RPM/TPM 控制速率，不控制总费用；max_tokens 控制单次最大输出，不保证累计费用。项目在既有 HTTPX 发送边界追加共享账本的累计预算硬闸，执行批次与翻译仍由上游负责。

**单轮必须使用合法 `--rounds 1` 与 profile `round_limit=1`。** 初期只查看 `_runtime_rounds` 的 yield 范围曾误建议 0；实际 `translation_start_target` 在 `current_round == round_limit` 时先 break 再生成任务，所以 0 会关闭首轮，1 恰好执行 `current_round=0` 一轮，下一轮先停止。CLI 也拒绝 `--rounds 0`。该误配置的零 token、原文输出即使 CLI exit=0 也不能算成功，修复后应重新生成 profile 并隔离空跑缓存。

模板单并发、`retry_count=0`、`enable_api_failover=false`、`untranslated_retry_limit=0`，关闭额外轮次与备用模型。`LLMRequester.sent_request` 把 0 次重试转换为至少 1 次尝试，正常只发首次请求。流式未知协议失败可能自动回退为另一次请求，所以模板 `enable_stream_api=false`。成功响应的稀疏补译原本另有请求，与 `retry_count` 独立，且未发现原生关闭开关；受限小样启动器在启用审计时关闭这一自动补译函数。请求数量和费用仍由 send 硬闸兜住，不能仅凭 exit=0 宣称模型已调用。小样初始 `max_output_tokens=4096`，可按估计输出长度调低。

## 请求硬上限、原始证据与 Qwen-MT 桥接

`request_audit.py` 在 `httpx.Client.send` 包一层请求计数与响应记录，不增加调度器。父进程给启动器 subprocess 增加以下环境变量：

```text
AINIEE_API_AUDIT_LEDGER=<四模型共同使用的绝对路径，例如 runtime/logs/pilot/shared-audit.jsonl>
AINIEE_MAX_API_POSTS=24
AINIEE_MAX_OUTPUT_TOKENS=4096
AINIEE_TOTAL_BUDGET_CNY=4.75
AINIEE_API_PRICES_JSON={"<verified-model-id>":{"input":0.0,"output":0.0}}
```

价格为每百万 token 的人民币峰值单价；此处 0.0 只是配置示意，必须替换核实的各模型单价，不能把示例当实际免费报价。缺少当前模型价格时拒绝发送。四模型每次 subprocess 共同使用同一个新格式账本，输入、输出和翻译缓存分别独立。账本放受忽略的运行目录。变量会从上游环境删除，不含 Key。不设置 ledger 时不启用 hook 或稀疏补译覆盖。

hook 只拦截百炼主机的 `/chat/completions` POST，在实际网络发送之前检查累计最多请求数、`max_tokens` 上限、普通模型 `enable_thinking=false`。精确模型 `ZHIPU/GLM-5.3-Flash` 必须 `enable_thinking=true` 且 `reasoning_effort=low`；其他普通模型不得开启。超出就抛 `RequestLimitExceeded`，额外请求不离开进程。模板显式 `enable_async_mode=false`，避免 aiohttp 绕过 HTTPX hook；启动器只测试同步 HTTPX 路径。

每次 send 前重读账本，次数继承所有 `started` 记录，不随 subprocess 重置；总金额为已完成且完整 usage 的峰价成本，加失败、usage 不完整或尚未完成请求的保守预留。新请求输入上界取最终请求体字节数加 2048；DeepSeek/Qwen 输出上界为 `max_tokens`，GLM 为 `131072 + max_tokens`，对可能不计入 max_tokens 的思考 token 预留。按配置峰值单价计算新请求预留，与累计金额相加超过 4.75 元就发送前拒绝，保留原充值的其余 0.25 元给连通性和不确定用量。

发送前的 `started` 记录 flush/fsync 落盘，进程在请求中途退出也留下预留。完成响应同时有输入与输出真实 usage 时按峰值价重新计算并释放多余预留；超时、失败或缺 usage 不释放。损坏账本、重复请求编号、缺少预留金额的旧格式账本拒绝继续计费。主流程按模型顺序单进程运行，此账本实现不支持多个独立 subprocess 同时写入；线程内有互斥，跨进程并行调用不得使用它冒充严格金额锁。

每次发送前写 `event=started`，完成后写 `event=completed`；网络失败写 `event=failed`。通过 `request_index` 对齐，不能把两行算成两次调用。记录请求体和完整响应正文，不记录任何 HTTP headers。递归遮盖 `sk-` 后字母、数字、点、连字符组成的新版分段密钥；也删除字典内 `authorization`、`api_key`、`api-key`、`headers` 字段。不会记录真实凭证文件内容。网络失败时 usage 未知，保留预留，不当零费用。

响应 `usage.prompt_tokens`、`completion_tokens`、`total_tokens` 和缓存/推理细分从真实服务器响应解析；只保留非负整数计数。正常 JSON 直接读取 `usage`，SSE 从最终携 usage 的数据帧提取，不依赖上游的成功翻译判定。因此格式失败且已消耗 token 的响应也能记账。

`estimated_cost_cny` 与 `reserved_cost_cny` 都记录发送前按字节与输出上界计算的预留；`input_tokens_upper`、`output_tokens_upper`、`peak_prices_cny_per_million` 保留计算依据。`usage_cost_cny_without_cache_discount` 基于真实输入输出 usage 与给定峰值单价，未扣缓存优惠；完整 usage 后以此替换预留，最终实际扣费以平台账单为准。未知价格拒绝请求，usage 不完整时实际成本字段为 `null` 且预留继续占用预算。

`qwen-mt*` 模型在同一 send hook 内转换专用请求：按顺序把原 system/user/assistant 提示内容拼成单个 user 消息，保留 `<textarea>` 和逐行编号契约；只传 `model`、`messages`、`max_tokens`、`stream`、`translation_options`，后者为 `source_lang=English`、`target_lang=Chinese`。不传普通模型的 `enable_thinking`、temperature 等字段。真实 40 条已调用并解析成功，但响应翻译复述了部分提示/背景，桥接效率与提示遵循并不理想；后续原生 `domains`/`terms` 优化前不能将本次视作最佳接入表现。详见[真实结果](trial-results.md)。

原始 usage 的其他查看位置：最终输出 `OUT/cache/AinieeCacheData.json` 中 `stats_data.token` 是输入加输出总和，`stats_data.total_completion_tokens` 是输出，未续跑的初次任务可用两者差值计算输入。`OUT/cache/ProjectStatistics.json` 只记录条数，不包含 token。`OUT/logs/session_*.log` 成功批次会出现 `提示消耗 N Tokens，补全消耗 M Tokens`。续跑和失败重试的上游累计口径可能遗漏或重置部分统计，费用应以每次 send 账本优先。

## 完整编号译文的包装兼容

主流程实际 Flash 第 5/6 次请求得到 HTTP 200 和完整 15+5 行中文编号译文，但模型没有输出外层 `<textarea>`，上游原解析器只认 textarea，因而原样写回英语。该情况已经消耗费用，主流程离线回收既有响应，不重跑这 20 条。

`format_compat.py` 只在现成 HTTPX send 返回边界提供保守兼容：响应 content 完全由 `N.正文` 行组成，每条正文非空且不能只有姓名；编号唯一且严格升序，并与本请求最后一个源文 textarea 的编号顺序完全相同，才增加 `<textarea>\n` 与 `\n</textarea>` 外层包装。译文、编号、标记、姓名、原有换行均不修改。重复、缺行、乱序、空正文、空白行、代码围栏和非编号额外说明一律不修复。截断/过滤结束原因也不修。

Qwen 单 user 请求可能包含系统提示里的 textarea 示例，兼容器按消息顺序连接提示后始终只取最后一个 textarea 源文，不取系统示例。已带包装的正常结果保持原样；不改上游 Reader、Writer 或调度规则。

账本 `response_body` 保留原服务器响应正文，`format_repair={"kind":"textarea_wrapper_only","matched_numbers":[...]}` 单独说明兼容动作；交给上游的是新的局部响应对象，原始证据不覆盖。SSE 仅保留现有 usage 提取，此格式兼容只针对当前小样使用的非流式 JSON。

真实 Flash 响应的脱敏冻结资源为 `tools/translation/upstream-runner/fixtures/flash-numbered-response.json`，记录来源账本第 5/6 次请求及响应 SHA-256。离线集成回放这两条响应，断言账本原响应逐字保留、Writer 输出 20 条中文、仅两次本地 HTTP 假请求，没有额外请求。

## 已完成验证

- 上游 CLI `--help` 正常退出；上游完整文本核心导入正常。
- 启动器 `launch.py --help` 正常退出，不触发任何翻译。
- 真实非交互首次启动曾在模型请求前遇到上游 WebUI 编译包安装提示，stdin 为 EOF 导致失败，未发 API。启动器已改为导入固定上游模块后，仅对 `translate` 且带 `--yes/-y` 的传统非交互任务跳过 `_check_web_server_dist` 的安装/更新检查，保留其三个队列状态初始化；没有下载 Web 包、启动 WebUI 或改 vendor 源码。主菜单自己的更新与安装行为保持上游原样。
- 启动回归真实构造 `CLIMenu`，读取现有 VNText 游戏原文样本，初始化并核对 `TaskExecutor`、Reader 与缓存管理器的连接；同时禁止 HTTPX、requests、urllib 网络和交互 Prompt。语言识别使用已有本地 MediaPipe 资源，其初始化诊断不影响结果。
- 新增独立无窗口子进程集成回归，从真实游戏样本的两条原文，经真实 CLI 任务契约、Reader、Executor、HTTPX 本地假响应和 Writer 完整走通。断言恰好一次 HTTP 请求、请求 `max_tokens=4096`、两条精确简体正文；合并真实上游 preset 后仍不转繁体，能复现零轮空跑与 cwd 缺少 regex 问题。该测试是离线集成，不是实际 LLM E2E。
- `test_bailian_compat.py` 的 3 个回归测试通过，覆盖百炼真实主机、伪造/其他主机、同步及异步请求器的 DeepSeek 分支。
- 审计与平台兼容的 10 个离线回归通过，覆盖 Qwen-MT 单 user/格式提示保留、额外字段剔除、发送前次数与金额硬闸、跨进程计数继承、完整 usage 释放预留、超时预留保留、未知价格拒绝、GLM 思考 low 参数与 131072 思考 token 预留、新版点号密钥脱敏及 headers 不入账本；加启动、路径、完整执行链、格式拒绝与真实 Flash 响应回放共 17 项。没有访问外网或真实模型。
- 配置与完整执行链确认：base URL、`extra_body.enable_thinking=false`、输出上限 4096、并发 1、`round_limit=1` 可真正发起一次本地 HTTP 假请求，而不只是进入配置对象。
- 真实试译后核查上游 root config 与 12 个已生成试译 profile：顶层及实际使用的 custom 平台 API Key 均为空，主配置无凭证字段。未启用的 sakura/murasaki/LocalLLM 继承上游公开占位，共 36 处，均与上游 preset 相同；不能写成“所有平台 Key 都空”。日志与账本的凭证字段及密钥模式扫描无命中；主流程另用本地完整 Key 的内存匹配核查待提交文件，凭证不入 Git。

真实调用验收已完成：四候选权限、模型名及附加参数接通，各 40 条输出和真实 usage 保存，全部正文等于冻结响应并按 manifest 关联；文风与忠实度的具体问题见[试译结论](trial-results.md)。并不代表全量缓存恢复或游戏汉化 E2E 通过。Windows 测试父进程默认 GBK 曾导致 UTF-8 子进程日志解码失败，集成测试捕获现显式 UTF-8，修复后离线链复验。
