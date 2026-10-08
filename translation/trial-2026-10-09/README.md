# 5 元预算真实试译输入

本目录从本机《Elsinore》真实游戏资源选择 40 条英文，原文合计 1,981 字符。输入制备不联网、不读取 API Key、不调用模型、不改写游戏；之后通过用户授权的百炼接口完成四候选各 40 条真实试译。

结果见 [comparison.md](comparison.md)、[verification.json](verification.json) 与[审读结论](../../docs/dev-tasks/localization/trial-results.md)。共 16 次批量请求、160 条译文，按实际 usage 与保守单价折算约 0.121 元（不含连通检查、不代表实际账单）。原始脱敏请求/响应保存在 `api-ledger.jsonl`，已付费样本不重复翻译。

- `inputs/01_hamlet_ghost_followup.json`：20 条同一路径相邻对白，位于 `Spine_OpheliaHamletStarter` 第 374–412 行。选择首次遭遇鬼魂后的 Quince/Ophelia/Hamlet 对话，并选择此前未见过暂停世界的内层分支；384/385 行与 387/388 行互斥，只保留前者。
- `inputs/02_register_challenges.json`：12 条不同场景的古雅、祈祷、讥讽、否定、内心话、富文本、乡音与角色称谓挑战。各条上下文独立，不把跨场景或互斥分支拼成连续对白。
- `inputs/03_ui_and_information.json`：8 条短分类标题、资料和知识标签，检查传闻、可能性、将来时、否定与行动对象。
- `manifest.json`：稳定 ID、文件/索引、原文、SHA256、资产哈希、确切原始行号与结构路径、语体及逐条只读背景。
- `context.json`：批次路径、只读上文、剧情事实证据行号和女性角色原文证据。
- `glossary.json`：统一比较用的暂定译法，全部标记 `proposal`。未经过用户确认，不能冒充正式锁定的术语表。
- `prepare_inputs.py`：只读真实资源、写入本目录的可复建脚本。不负责执行翻译调度。

采用 AiNiee-Next VNText 的 `name`/`message` 输入结构；模型专用背景从 `context.json` 和 `manifest.json` 单独传入。工具输出可能丢弃额外元数据，回收时按文件和索引恢复 ID，并检查条目数量、原文与占位符/标签。译文的 ID 不能靠模型自行猜测。

文风沿用项目约定：日常对白清楚顺口，保留原文已有的少量戏剧感；戏中戏、祈祷及格言稍凝练；粗犷口语、讥讽不雅化；资料和 UI 优先准确。现代小说口语、网络梗和统一文言化均不是目标。`Lady Rosencrantz`、`Lady Guildenstern` 具有游戏内女性证据，不能套用《哈姆雷特》原著的男性设定。

第一批先前独立 `if` 块不在这 20 条内；仅依据本段不能推断它们的所有真假状态，也不能把先前循环台词加进背景。资源选择沿用最大载荷候选，尚未动态确认它就是游戏加载的文本版本；样本不是全量语体统计或游戏剧情验收。

如需复建输入，可在项目目录执行：

```powershell
python translation/trial-2026-10-09/prepare_inputs.py
```

该命令会重写本目录的 `inputs`、`manifest.json`、`context.json`、`glossary.json`；不会修改其他目录下的模型译文。已有译文按原清单关联后，不要混用后来重新选择的样本。
