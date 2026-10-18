# 特殊章节资料提示、未完句与命运用词

状态：候选已验证，尚未安装。相对上一候选变化5条：命运步调4个源和未完句1条；合计60词条待安装。插件1.5.15，17,069词条、157规则、字体7,661，无新增字符。

## 最新截图未完句

英文：`There's... it can't be. This must be another trick.`

改前：有……不可能。这一定又是个骗局。

改后：这……不可能。这一定又是个骗局。

来源：scenes载荷ed4319ff…的Spine_PoloniusQuestions。开头没有说完，不能断言后面原本要说something wrong；中文用这保持断续反应，不补未说出的内容。

## 命运用词

按用户进一步反馈，将前一候选“命运运转得太慢”改成“命运转动得太慢”，避免运字重复，并衔接下一句转动轮盘的意象。王后／贝尔纳多两个分支的资源与双层斜体同步。

## 王后资料提示

StartingThingy开场重新assert encountered(gertrude)，还初始化其他角色。实际程序中，LeadUpdater按条件激活条目；Model.formatGroupedLiterals在bio类型的LEAD_ACTIVE状态变化上生成“Ophelia learns more about … Their Character Bio … will be updated …”通用提示，没有在这里比对玩家上次读过的正文是否新增了信息。

截图的段落顺序对应bios载荷7719667e…中的initial、gertrude2、gertrude4：初始介绍、日记中的私情、奥地利出身。对应英文均有完整译文，三段组合及4个原子共6项真实XUnity离线消费者通过。该版本gertrude3为失眠段，active为false，截图不出现不能算漏译。

因此未发现缺失的新译文；结合特殊章节初始化，提示可来自旧资料重新启用／重组，而非保证增加新的剧情段落。没有读取玩家存档或重放当次通知，不能声称确认了该次内部变化的具体原子序列。

## 昆斯原著称谓

查阅[译林出版社朱生豪译本人物表](https://detail.youzan.com/show/goods?alias=2fp35egktqtmx&from_source=gbox_seo)：昆斯为木匠，戏中戏念开场白；掌戏乐之官属于菲劳斯特莱特。未找到本作Playmaster可直接照搬的同一原著称号；班主候选被用户否定，未作全局替换。

## 编译规则与维护方式

直接读取Elsinore.dll的CompilerPasses.doTextReplacement，确认九次String.Replace的输入及顺序与prepare_lead_followup.runtime_source一致。幽灵整段斜体来自另一项CompilerPasses.italicizeAllDialogueOf。

确定格式变体可以按真实源规则派生英文查找键，并复用同一审定中文、只附加对应格式；中文标点本身按中文规范表达，不必再跑英文破折号转换。输出词表保留多个英文键与维护多个独立中文译文是两回事。现有显式别名已有部分采用此模式；本轮核实规则并完成缺陷校订，尚未将全部历史变体迁移成单一中文维护来源。

## 验证

- 旧候选实际复现11项不符；更新后112项范围消费者、18项受影响既有消费者、6项王后资料消费者通过。
- 19+4+7项治理／回归通过；708组变体、33条显式别名检查通过。
- 导出前后精确变化5个词条，无新增字符；40文件与候选ZIP逐项一致。
- 未启动主游戏、未访问存档、未安装，不称画面或剧情E2E通过。

详见[核验证据](../../../runtime/evidence/perfect-day-feedback-verification-2026-10-19.json)。

## 本轮全部改前／改后

1．英文：There's... it can't be. This must be another trick.

改前：有……不可能。这一定又是个骗局。

改后：这……不可能。这一定又是个骗局。

2．英文：<i>Do not hate him, my love. His hand was forced by the plodding pace of fate.</i>

改前：<i>不要恨他，我的爱人。命运运转得太慢，才逼得他动了手。</i>

改后：<i>不要恨他，我的爱人。命运转动得太慢，才逼得他动了手。</i>

3．英文：<i>And do not hate Claudius, my good man. My brother's hand was forced by the plodding pace of fate.</i>

改前：<i>也不要恨克劳狄斯，我的好伙计。命运运转得太慢，才逼得我弟弟动了手。</i>

改后：<i>也不要恨克劳狄斯，我的好伙计。命运转动得太慢，才逼得我弟弟动了手。</i>

4．英文：<i><i>Do not hate him, my love. His hand was forced by the plodding pace of fate.</i></i>

改前：<i><i>不要恨他，我的爱人。命运运转得太慢，才逼得他动了手。</i></i>

改后：<i><i>不要恨他，我的爱人。命运转动得太慢，才逼得他动了手。</i></i>

5．英文：<i><i>And do not hate Claudius, my good man. My brother's hand was forced by the plodding pace of fate.</i></i>

改前：<i><i>也不要恨克劳狄斯，我的好伙计。命运运转得太慢，才逼得我弟弟动了手。</i></i>

改后：<i><i>也不要恨克劳狄斯，我的好伙计。命运转动得太慢，才逼得我弟弟动了手。</i></i>
