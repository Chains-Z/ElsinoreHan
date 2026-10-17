# 布莉特首次盘问时间线校订

状态：候选已验证，尚未安装。用户游戏正在运行，未覆盖主游戏补丁、未启动游戏、未访问存档。见[候选核验](../../../runtime/evidence/brit-question-verification-2026-10-18.json)。

## 原文与改动

真实`schedule`资产SHA256为`c9729c297f9df2d9442f9c899cb1fd2754ffe1af054ed24e385da837fa708f47`，第3905行、事件`SC_ASSN_BritInterrigationOne`的`description`为`Bernardo begins to question Brit.`，原词条`ui-b9647fadcdd2d009`。旧译“贝尔纳多开始询问布莉特。”，按用户确认改为“贝尔纳多开始盘问布莉特。”。

对应`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`，`ASSN_BritInterrigationOne`第8788行起。贝尔纳多出示信件和军事地图证据，并以她的家人施压，question在此译为盘问更贴合语境。后两次描述用interrogate，继续保留“审问”；不据此断言作者有意划定不同法律程序。

通过既有`timeline-label-corrections.json`记录旧值、准确来源及源哈希后应用，未修改冻结输入、输出或原始模型响应。

## 验证

- 首次盘问、后两次审问3项真实XUnity逆序首匹配、递归上限64的消费者通过，16项导出治理测试通过。
- 导出相对已安装版本仅本条变化；17,068词条、157规则及中文字集合不变，字体、插件、动态词表无需改动。
- 通过`package-full.ps1 -PendingInstall`生成候选，40文件与ZIP逐项一致。相对已安装包仅正文词表和候选状态说明改变。
- 本轮是文字与组件核验，不代表重跑时间线UI、物理F8或完整剧情端到端测试。后续仍须确认游戏退出并通过安装器更新。
