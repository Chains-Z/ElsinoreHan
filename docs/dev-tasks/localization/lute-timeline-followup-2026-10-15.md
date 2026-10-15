# 鲁特琴搜寻时间线简介

用户反馈星期五找到鲁特琴的事件却显示“贝尔纳多和哈姆雷特继续寻找，却毫无结果”。经继续核查，按用户指定保留 `fruitless`，校订为：

> 贝尔纳多和哈姆雷特此前没有收获的搜寻仍在继续。

原文为 `Bernardo and Hamlet's fruitless search continues.`。原版措辞可以描述此前没有收获、目前仍在继续的搜寻；旧译“却毫无结果”容易被理解为整场最终失败，直接省略 `fruitless` 又丢失信息。不把作者笔误或失败分支串用当成已证实事实。

## 来源与分支核查

只读真实Unity对象表：`resources.assets` 中 `schedule` 的path ID 448（SHA256 `c9729c297f9df2d9442f9c899cb1fd2754ffe1af054ed24e385da837fa708f47`），其 `events[207]` 是 `SC_BOYS_Meeting3`，scene为 `BOYS_Meeting3`，room为 `path`。该记录只有一条固定description，不存在成功/失败两份简介。

对应真实 `scenes` 为path ID 474（SHA256 `6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`）：

- `BOYS_Meeting2` 在城墙搜寻，12598行明确鲁特琴不在那里，结束后邀请第三场。
- `BOYS_Meeting3` 范围12605至12711行；12660行的可选分支影响人物谈话，12679行在共同流程明确找到琴，12687行之后才按雷欧提斯是否去巴黎分支讨论归还，没有“未找到”的正常完成结局。
- 真实程序集中的 `Invoke_BOYS_Meeting3__SC_BOYS_Meeting3__3/4/5` 分别包含找到琴、询问是否找到及琴完好干燥的对白，三个方法均没有条件跳转。时间线 `tooltipForItem` 按事件ID查找并读取Description，`get_Description` 直接返回字段；未发现根据剧情分支选择其他简介的路径。程序集SHA256 `69e348fc4180302fc38724ec8ee5609e7fc94b59622dcab881ce44cc0b2fe6af` 与既有审计一致。

以上为原资源与编译代码静态核查，没有启动游戏或执行剧情E2E。

## 校订与交付

通过既有 `timeline-label-corrections.json` 治理层应用，准确旧值、原文SHA及来源均保留，不改原始补译审计或冻结模型输出。3项独立简介、未来事件提示与详情富文本封套的真实XUnity消费者、15项导出治理检查均通过。仅一行译文变化，中文字符集、动态规则、字体、插件、配置与许可均不变，40文件候选目录与ZIP逐项一致。游戏仍在运行，本轮只更新候选，不安装、不创建备份。候选结果见 [核验记录](../../../runtime/evidence/lute-timeline-verification-2026-10-15.json)。
