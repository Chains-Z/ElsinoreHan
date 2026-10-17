# 结局确认页图片标题补译

状态：1.5.9已通过核验并安装，包含此前1.5.8书页去字与层级修复；见[候选证明](../../../runtime/evidence/ending-confirmation-verification-2026-10-17.json)与[安装证明](../../../runtime/evidence/ending-confirmation-install-verification-2026-10-17.json)。未启动用户游戏、未推送远程。

## 根因与修复

用户重温疯人院结局后，结局确认页的REALITY/JOY已经翻译，Sacrifice/for仍为英文。此前仅拦截EndingSelectUI.populate，使用2048×1400的UI_Book_BackGround2；确认页则由GameOverUI.Activate驱动，使用916×1252的UI_Book_Unlock，根本没有创建连接词翻译层。它与主书页不是同一张图。

新增GameOverUI.Activate后置处理，绑定EndingUnlockTexture、EndingUnlockPage和EndingTitleWhat。两种页面共用笔画重建与TMP逻辑，但各自核验尺寸、DXT5区间及SHA256、笔画区域和行中心；来源见[单页契约](../../../translation/supplemental/ending-confirmation-paper-source.json)。只在内存清除英文笔画，不覆盖游戏资源、不拼贴纸面、不打包原图。原生64号关键词保留各自样式，连接词为51.2号斜体并沿用原生墨色。F8恢复真实英文背景，页面隐藏时关闭中文层并恢复背景。

## 验证与安装

- 5项Python像素测试与8项C#纯逻辑断言通过。新增单页来源覆盖916×1252布局、标准DXT5逐像素对照、笔画区域、透明度及四条分隔线。两种背景的实际运行重建字节都与离线消费者完全一致。单页掩码8,336像素、实际变化7,208像素，掩码外及透明度不变。
- 隔离运行`bcde3c8d69474128b3fa84c36cd8982a`通过真实ActivateBook及11页翻页、22次F8与左右悬停层级回归。再通过真实ActivateGameOver入口打开已解锁的END_Delusion确认页，检查四行中文、样式、位置、F8原图恢复、页面隐藏/恢复，并在相同真实TMP控件重放全部13组资源标题。不改变activeEnding，不解锁其它结局，不点击选择命运或重启按钮。
- 确认页回归以缺少翻译层明确失败，不能拿关键词已翻译代替图片标题完成。测试首次运行失败：探针把EndingId.ToString误当裸ID，实际值为Ending(END_Delusion)；菜单诊断又漏配当前字体名称。改为构造同类型ID比较，并提供当前字体名后重跑通过；旧失败证据保持原状态。
- 导出真实背景及字形网格，生成四张软件合成预览，人工查看新增确认页：无英文残留、纸块和分隔线重叠。SDF边缘为近似，不称GPU截图或完整剧情E2E。
- 13项启动前保护测试通过。探针无窗、静音、低优先级、10FPS；业务初始化前重定向克隆存档并拦截保存及迁移。退出后清除临时存档、探针及appid，恢复加载器配置原字节，原8个存档的哈希、时间和数量未变。
- 安装前确认用户游戏退出，通过项目安装器安装后再生成正式本机包；40文件与ZIP逐项相符。原exe、UnityPlayer.dll、resources.assets及Assembly-CSharp.dll的哈希、大小与时间均未变。字体、词表及配置字节不变，没有创建备份。
- 安装后附加存档核验曾因PowerShell将JSON时间自动转为DateTime而错误报告变化；随后逐项确认哈希一致，并按UTC ticks比较时间，8项全部一致。该错误来自核验表达式，未再次安装或改写存档。

## 同轮剧情脚本查询

用户另问只警告波洛涅斯、不警告贝尔纳多时谁会遇害。只读真实主scenes资源（SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`）与schedule：

- 普通`Spine_HamletAndGertrude`分支中，`believes(polonius,hamlet_threat)`为真时，`HAMGERT_PoloniusThere`让父亲逃出呼救，跳过刺死父亲。
- 同一条件令主场景调用`HAMGERT_AftermathNoOne`。王后在冲突中刺死哈姆雷特，脚本断言`dead(hamlet)`；随后她自尽，断言`dead(gertrude)`。因此正常流程下只警告父亲，遇害的是哈姆雷特和王后，不是贝尔纳多。
- `Spine_HamletAndGertrude_PlusBernardo`由贝尔纳多获知`hamlet_threat`的调度分支进入，调用现行`HAMGERT_AftermathBernardo`：贝尔纳多推倒并打昏哈姆雷特，明确说明只是昏迷，没有死亡断言。资源中的`HAMGERT_AftermathBernardoOld`确实含死亡，但现行主场景不调用它，不能据此推断现行结果。

以上是其它事件照常发展时的局部分支，不代表整轮所有人物的最终存活；未修改游戏脚本。
