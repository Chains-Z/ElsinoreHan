# 哈姆雷特姓名与摆件玩笑校订

状态：候选已验证，尚未安装。未启动、操作主游戏或访问存档，见[候选核验](../../../runtime/evidence/hamlet-name-verification-2026-10-18.json)。

`p05316-6f4f165eab4d`，真实`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`，`GuilRomance2`第14005行：

> It sounds like the kind of thing you'd put in a room to decorate a corner. 'Oh, and here's an antique vase, next to that Hamlet over there. Brightens up the room.'

前句吉尔妲说见过各种怪事，例如一个丹麦男孩竟然叫Hamlet，随后把名字当成摆件名称，假装介绍室内陈设。没有查得装饰品词义或明确的谐音依据，不另造谐音、具体摆件类别或词源解释。用户确认点明这段主观怪联想，最终译文：

> 这名字听着不像人名，倒像某种摆在墙角的装饰品。“噢，还有这只古董花瓶，就摆在那边那个‘哈姆雷特’旁边。给房间添点亮色。”

只修此句，不改前句对名字的调侃、后句相信女主的条件，也不全局更名。

- 通过`local-corrections.json`应用，记录准确旧值、源文哈希与资源出处，冻结输入、raw、outputs和审计未变。
- 18项导出治理测试、4项真实XUnity递归消费者通过，覆盖裸句、对话框行高封套、日志单句和相邻三句组合，核对原文斜体及姓名到摆件的衔接。
- 相对上一候选只改此句；17,068词条、157规则、中文字集合不变，字体、插件、动态词表不变。
- `package-full.ps1 -PendingInstall`生成候选，40文件与ZIP逐项一致，包含此前全部候选修复。本轮为组件与词表验证，不代表实际画面、物理F8或完整剧情端到端验收。
