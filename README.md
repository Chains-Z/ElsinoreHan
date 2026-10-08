# ElsinoreHan

《Elsinore》的汉化研究与后续补丁项目。目标是制作能在游戏内显示中文的版本，先开始玩，再随游玩校对。

当前已完成文本提取、现成 AI 翻译工具/提示词/模型调研，准备了 217 条真实试译输入，并安装离线中文样板。主菜单三个按钮中文渲染通过，后台静音自动导航设置页及组件检查通过。尚未调用翻译模型；设置页像素排版、对白、资料页和全量文本覆盖率仍待验收。

## 目录

| 路径 | 内容 |
| --- | --- |
| `AGENTS.md` | 新会话的项目约定与上下文入口 |
| `docs/dev-tasks/localization/README.md` | 分析结论、实施方向、费用假设与待办 |
| `analysis/analyze.py` | 只读提取脚本 |
| `analysis/text_inventory.json` | 待译候选清单，含原文、来源和类别 |
| `analysis/assembly_review.json` | 程序集中额外待审核的字符串 |
| `analysis/metrics.json` | 统计与分析局限 |
| `docs/dev-tasks/localization/research-projects.md` | AiNiee / GalTransl 的版本、输入契约和复用建议 |
| `docs/dev-tasks/localization/research-style-models.md` | 自然中文提示词、skill、模型候选及盲评流程 |
| `docs/dev-tasks/localization/register-evidence.md` | 真实原文语体与适度保留戏剧感的约定 |
| `translation/pilot/` | 真实 VNText 试译输入和来源映射，无模型译文 |
| `tools/translation/prepare_pilot.py` | 本地试译输入适配器 |
| `tools/patch/` | 离线样板安装与游戏内自动验证工具 |
| `docs/dev-tasks/localization/technical-probe.md` | 游戏运行验证结果、证据与局限 |

## 重新分析

使用已安装 `pefile` 的 Python：

```powershell
python .\analysis\analyze.py
```

脚本默认读取 `D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data`，只向自身所在的 `analysis` 目录写分析结果。若游戏路径改变，更新脚本里的 `GAME`。

下一步采用现成翻译执行器，用同一批真实资料比较候选模型的准确性和中文语感，确定术语与文风后批量预译；并继续验证对白与资料界面的文字显示。语体默认易读，仅保留原文已有的古雅和戏剧感。
