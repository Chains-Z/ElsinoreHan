# 聚会死亡玩笑与奎因斯对白校订

状态：候选已验证，尚未安装。未启动、操作主游戏或访问存档，见[候选核验](../../../runtime/evidence/party-dialogue-verification-2026-10-18.json)。

## 三句校订

真实`scenes`资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`，场景均为`GUILD_Party`。

- 第25192行，`p09034-362db4afaf05`：`Well, <i>that's</i> horribly morbid. Lady, I like your style.`用户确认由“阴沉”改为“晦气”，回应伊尔玛说两人死期不远的死亡话题，保留欣赏其趣味的反差及斜体。最终为“哎呀，<i>这话</i>可真够晦气的。女士，我喜欢你这风格。”。
- 第25197行，`p09036-fd85d11e8186`：`Ah, my good Marcellus, how kind of you to call upon me.`旧译“好马塞勒斯”机械翻译称呼；用户又指出“承蒙你点名，真是客气”不自然。最终为“啊，亲爱的马塞勒斯，多谢你想到我。”，保留奎因斯带笑故作客气的语气，回应马塞勒斯问他是否也任由姑娘们说自己没用。
- 第25198行，`p09037-7d1fd7068b9b`：`As a master of the stage, my position is behind the curtains, out of sight and mind.`用户指出“被人惦记”偏向关切、牵挂，且失去并列节奏。最终为“身为舞台的掌控者，我的位置在幕后——无人看见，无人想起。”，末尾用两个四字句保留不被看见、不被想到的语义与节奏。

奎因斯随后说`Therefore, I have little interest in this debate.`，因此本轮没有补写他必须加入争论、感到荣幸或对马塞勒斯抱有恋爱感情。没有全局替换`my good`或`morbid`。

## 验证

- 三条校订通过`local-corrections.json`导出层应用，记录准确旧值、源文哈希和资源出处，冻结输入、raw、outputs和审计未变。
- 11项真实XUnity递归消费者通过，覆盖三句正文、对话框行高封套、日志单句，以及伊尔玛／吉尔妲／马塞勒斯和马塞勒斯／奎因斯的前后对白组合；18项导出治理测试通过。
- 相对上一候选只改上述三条；17,068词条、157规则、中文字集合不变，字体、插件、动态词表不变。
- 使用`package-full.ps1 -PendingInstall`生成候选，40文件与ZIP逐项一致，包含此前全部候选修复。本轮为组件与词表验证，不代表实际画面、物理F8或完整剧情端到端验收。
