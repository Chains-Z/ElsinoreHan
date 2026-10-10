# 2026-10-10 时间线状态与宗教类别文案

本轮保留候选1.5.0的两个时间线标签及对应前缀校订。宗教称呼按用户最终意见保留原译，插件、解析语法及游戏条件不变。仍待用户保存退出后安装。

## 时间线状态

用户截图的悬停标签 `Unlikely event:` 与详情 `This will not happen based on current conditions.` 对应同一个 `IsImpossibleEvent` 类型。只读真实 `TimelineUI.tooltipForItem` 的IL确认：未来分支显示 `Unlikely event:`，过去分支显示 `Impossible event:`；`createEventContent` 分别显示“按当前条件不会发生”和“该事件未发生”。

因此按实际功能统一中文：

| 原标签 | 新译文 | 对应状态 |
| --- | --- | --- |
| Unlikely event: | 当前条件下不会发生的事件： | 时间尚未到，当前条件阻断，不是概率低 |
| Impossible event: | 未发生的事件： | 时间已过，详情确认未发生 |

没有把未来标签写成永久不可能，也没有改动事件判定。精确词条及组合前缀同时校订，避免单独显示与带正文时不一致。来源脚本 `audit-timeline-labels.ps1` 与 `timeline-label-source-audit.json`，治理记录 `timeline-label-corrections.json`。

## 霍拉旭的 devas / asuras

截图原句为：`That's correct, yes. I am a <i>heathen.</i> I prefer my devas and asuras. Some wisdom here, a little trickery there... Gods with real <i>personality.</i>`

两个词是复数类名，不是两位神的个人名字。“提婆”是deva有出处的音译。曾建议改为“天神”，用户认为没有必要，最终明确保留“提婆和阿修罗”；对白及人物简介两源均已恢复。保留原有斜体和叙述者口吻。审校意见记录在religious-term-reviewed.json，未接入导出校订层。

最终保留对白：

> 对，没错。我是个*异教徒。*我更喜欢我们信奉的提婆和阿修罗。有的颇有智慧，有的耍点诡计……这些神才真有*个性。*

依据：[印度教出版机构Himalayan Academy词汇表](https://www.himalayanacademy.com/media/books/merging-with-siva/web/glossary_a.html)将deva解释为神或神灵类别；[法鼓山官方说明](https://tl.ddm.org.tw/default-ddmtw/xmnews/cont?qcat=0K297401756442626214&sid=0K305398770129523300&xsmsid=0K297379120077217595)明确“天”的梵语音译是提婆（Deva）。后者用于核对音译，不将佛教教义直接套入霍拉旭的信仰。来源和用户决定记录为 `religious-term-reviewed.json`。

## 验证与交付边界

10项定向真实消费者、56项旧界面、92项时间线、616项通知、738项全部人物简介子集，共1512项通过；15项导出治理及39项资料判定器检查通过。姓名/富文本/条件解析语法和插件二进制未变，未重复此前完整矩阵或重型页面、滚动验收。

原始响应和原资源没有改动，中文字形集合仍为2816字。候选ZIP重新生成并核对，不包含存档或诊断插件；主游戏进程仍在运行，未安装。本轮摘要为 `runtime/evidence/timeline-religion-followup-verification.json`。此前运行 `c260fdd...` 和128408项矩阵仅作候选基线证据，不冒称其包含本次四条新译文。

用户撤回宗教词替换后的最新候选：10项定向加738项人物简介消费者，共748项通过；15项导出检查通过。候选包重新生成并核对，最新哈希见runtime/evidence/retained-deva-verification.json。前述1512项及timeline-religion-followup记录是586fd5b阶段历史证据，不改写历史结果。
