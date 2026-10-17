# 布莉特订婚追问介词修正

状态：按用户“改，安装”指令修订，并连同此前调情打趣校订安装；插件保持1.5.9。见[候选核验](../../../runtime/evidence/brit-betrothal-verification-2026-10-17.json)及[安装核验](../../../runtime/evidence/brit-betrothal-install-verification-2026-10-17.json)。

## 原文与修正

`s00175-cb53f9849d9e`，真实`scenes`资产的`QUEEN_Coronation`第15107行，资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`。克劳狄斯刚宣布`Lady Ophelia and I are to be betrothed. Today.`，布莉特以`[surprise] {Ophelia_Surprised}`追问`To—<i>Ophelia?</i>`。

这里的to承接betrothed to，表示与谁订婚，旧译“给——<i>奥菲莉娅？</i>”误解了介词。改为：

> 和——*奥菲莉娅？*

保留原文破折号、疑问和姓名部分斜体。通过`local-corrections.json`的`apply_at_export`应用，记录准确旧值、来源及源哈希；冻结输入、raw、outputs及审计不变。

## 验证与安装

- [订婚消费者夹具](../../../translation/supplemental/brit-betrothal-tests.json)绑定真实角色、场景、行号，覆盖裸句、布莉特日志和包含订婚公告的相邻对白组合；3项真实XUnity逆序首匹配、递归上限64的组件消费者通过。另复验此前调情打趣3项消费者，共6项通过。
- 15项导出治理测试通过。此次导出相对上一候选只改本句；相对安装前词表精确为本句及“你这姑娘，胆子可真不小。”两处替换。17,067词条、157动态规则及全部中文字集合不变。
- 先生成并核对待安装候选，确认游戏已退出后通过`install-full.ps1`安装，再生成正式本机包。40文件与ZIP逐项一致；正文外的插件、字体、动态词表、配置与许可字节不变。
- 安装前后核对原游戏4文件和全部8个真实存档的哈希、修改时间、大小及数量，均未变化。未启动游戏、未创建备份；本轮为离线来源与组件核验及安装校验，未执行UI像素或完整剧情端到端验收。
