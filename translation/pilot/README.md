# 真实游戏原文试译样本

本目录只准备输入，没有调用翻译模型，也没有中文译文。沿用 [AiNiee-Next](https://github.com/ShadowLoveElysia/AiNiee-Next) 的 VNText 输入契约，避免另写翻译调度器。

- `input/dialogue/`：两个完整脚本段落，共 187 条带说话人的对白。
- `input/documents/resource_ui.json`：30 条真实书信、资料和标题。
- `manifest.json`：每条原文的来源、哈希、脚本行号及原始表演提示。

脚本标签不代表游玩顺序：`Spine_OpheliaAloneStarter` 包含返场内容，`Spine_OpheliaHamletStarter` 包含不同条件下的对白。样本可能涉及剧透。顺序为资源内排列，互斥分支不能当作同一次连续对话。这里选择最大 `scenes` 候选载荷，尚未证明它是实际游戏加载的版本。

## 使用边界

AiNiee-Next 的 VNText reader 会把 `[name]message` 送入模型。writer 会丢弃自定义 ID 与来源字段，因此把这些信息独立保存在 `manifest.json`。回收译文时必须核对文件和条目数量并按原顺序关联，不能因为 JSON 能解析就认为翻译完整。

默认 VNText 输入没有携带分支条件或 `acting_cues`。不能声称当前样本已解决完整剧情上下文。实际试译前须从脚本确认路径，对需要区分的分支另行分批，必要的事实放进场景背景；不要让模型自行补全背景。

对白与文档应分别选取语体规则；不要把信件统一写成口语，也不要把所有对白古文化。候选 prompt、模型和盲评办法见 [风格调研](../../docs/dev-tasks/localization/research-style-models.md)。外部工具默认的日译中或 ACGN 规则需替换。

## 重建

使用现有 Python 与 `pefile`，从真实游戏资源重建到一个新的空目录：

```powershell
python tools/translation/prepare_pilot.py --output translation/pilot-rebuilt
```

脚本不覆盖非空目录，不联网，不修改游戏。`--dialogue-target` 是最低目标，提取会继续到当前脚本段落结尾，因此条数可能高于目标。它只解析明确的单行角色对白，是试译输入适配器，不是完整剧情提取器。

```powershell
python -m unittest discover -s tools/translation -p 'test_*.py'
```

已通过 4 项离线测试：转义、注释行号、排除程序字符串和保留完整段落。这不证明译文质量或游戏内显示效果。
