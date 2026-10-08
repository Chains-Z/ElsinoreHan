# ElsinoreHan

《Elsinore》的汉化研究与后续补丁项目。目标是制作能在游戏内显示中文的版本，先开始玩，再随游玩校对。

当前完成了引擎识别、文本提取、初步成本估算和参考项目分析。尚未安装补丁、调用翻译 API 或验证游戏内中文显示。

## 目录

| 路径 | 内容 |
| --- | --- |
| `AGENTS.md` | 新会话的项目约定与上下文入口 |
| `docs/dev-tasks/localization/README.md` | 分析结论、实施方向、费用假设与待办 |
| `analysis/analyze.py` | 只读提取脚本 |
| `analysis/text_inventory.json` | 待译候选清单，含原文、来源和类别 |
| `analysis/assembly_review.json` | 程序集中额外待审核的字符串 |
| `analysis/metrics.json` | 统计与分析局限 |

## 重新分析

使用已安装 `pefile` 的 Python：

```powershell
python .\analysis\analyze.py
```

脚本默认读取 `D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data`，只向自身所在的 `analysis` 目录写分析结果。若游戏路径改变，更新脚本里的 `GAME`。

下一步是验证少量文字的游戏内替换和中文字体，然后组织全量预译与词表生成。
