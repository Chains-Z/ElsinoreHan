# 序章称呼、远行与卫兵口语校订

用户反馈三处译文：伊尔玛把奥菲莉娅称作“迈克”、赴巴黎被说成“出门”、马塞勒斯的口头停顿生硬。用户明确要求保留“资历最老”。

最终修订：

- p15078：`Ay, Maike... What's got your father all in a rush so?` → “哎，姑娘……你父亲怎么急成这样？”
- p15079：`Laertes heads to Paris tomorrow. I think Father's merely overly worried about his departure.` → “雷欧提斯明天就要去巴黎了。我想父亲只是太担心他这次远行了。”
- p15096：`Besides, some of the other boys thought that maybe, yeh know, the most senior guard ought not to gamble as much...` → “再说，其他几个小伙子觉得，资历最老的卫兵嘛，也许不该赌得那么勤……”

Maike原文并非Mike，游戏只有一例，DLL与资源一致。[德国民间舞协会的说明](https://volkstanz.de/volkstanzwissen/taenze/maike)明确记录其在威斯特法伦方言中表示女孩，并举直接称呼女孩的例句。结合本句对奥菲莉娅说话，判断为“姑娘”；未找到本游戏作者注解，不能称作者确认，也不将该方言归为伊尔玛故乡的语言。departure由赴巴黎的前句限定为这次远行，不补写旅途危险、反对或舍不得等心理。yeh know用“嘛”承接口语感，保留maybe的推测及“资历最老”。

三处正文修订记入local-corrections.json，带原文哈希、原译文、来源与理由；apply_at_export仅在正式导出层应用。b0102输入、raw、输出和原审计字节未改。词条仍17,027、规则仍138，动态字典哈希不变，中文字符集合仍2,816。

9项真实XUnity消费者覆盖三条单句、带人物标签和混合日志；15项导出回归通过。对白/混合日志派生预期已更新，未重跑114,028项矩阵或剧情E2E，不把重生成当作通过。验证与安装摘要：runtime/evidence/playthrough-text-verification.json。正式词表、个人包目录与ZIP哈希一致，游戏四个二进制文件不变；备份runtime/backups/full-9a91b7d7ab3e451baf77ce56dded4f80。

同轮用户反馈重置存档进入序章后27FPS与音量小，后在重启游戏后立即恢复，明确取消性能/音量排查。主目录未见RuntimeProbe，正式插件不设置帧率/音量，原游戏启动逻辑设置targetFrameRate=60；这些只读证据不能确认重置存档就是直接原因。没有继续诊断、修改性能/声音设置或干预用户游戏。已启动的Steam检索未得到可用于确认序章问题的结果，不声称存在社区共识。
