# ElsinoreHan

《Elsinore》的汉化研究与后续补丁项目。目标是制作能在游戏内显示中文的版本，先开始玩，再随游玩校对。

当前已完成文本提取、现成 AI 翻译工具/提示词/模型调研，并通过 AiNiee-Next 对同一组 40 条真实原文完成四模型试译，共 160 条译文。批量 API 用量折算约 0.121 元，所有译文与冻结响应及原文来源已核对；模型仍存在意义和措辞问题，详见[实测结论](docs/dev-tasks/localization/trial-results.md)。离线样板的主菜单中文渲染、后台静音设置导航及组件检查已通过；设置页像素排版、对白、资料页和全量覆盖率仍待验收。

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
| `translation/provider.json` | 百炼业务空间、公开接口地址和模型名，不含密钥 |
| `translation/trial-2026-10-09/comparison.md` | 四模型 40 条真实原文的完整译文对照 |
| `docs/dev-tasks/localization/runner-setup.md` | 现成执行器配置、预算闸与离线回归说明 |
| `tools/translation/prepare_pilot.py` | 本地试译输入适配器 |
| `tools/patch/` | 离线样板安装与游戏内自动验证工具 |
| `docs/dev-tasks/localization/technical-probe.md` | 游戏运行验证结果、证据与局限 |

## 重新分析

使用已安装 `pefile` 的 Python：

```powershell
python .\analysis\analyze.py
```

脚本默认读取 `D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data`，只向自身所在的 `analysis` 目录写分析结果。若游戏路径改变，更新脚本里的 `GAME`。

下一步使用已冻结的真实模型译文，继续验证对白与资料界面的加载、字体和排版；定向改进惯用语、省略状态和增译规则后批量预译。语体默认易读，仅保留原文已有的古雅和戏剧感。
