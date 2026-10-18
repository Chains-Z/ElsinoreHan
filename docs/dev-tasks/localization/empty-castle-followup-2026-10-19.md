# 空城堡独白校订与码头旧稿纠正

状态：用户确认的3句已进入候选，累计15词条待安装。未启动游戏、安装或访问存档。

## 三句完整改前／改后

英文：I could never have been the savior you wanted. Not really.

改前：我从来都不可能成为你想要的救世主。真正意义上的救世主。

改后：我从来都不可能成为你期望的救世主。真的不可能。

Not really承接前面的否定，不作为孤立名词短语补充；采用用户确认的强调否定句。

英文：When the Book erased them, where did they go, I wonder?

改前：那本书抹去他们的时候，他们去了哪里呢？

改后：我在想，那本书抹去他们以后，他们都去了哪里？

原来的疑问句末呢已传达自问，不将其误报为漏译；按用户确认显式写出我在想。

英文：I fear you and I shall never be together, Mother.

改前：母亲，我怕我们永远也无法团聚了。

改后：母亲，恐怕我和你永远也无法团聚了。

用恐怕表达忧虑判断，保留我和你的直接称呼。

来源为真实scenes_enviro资产430eb8bd…，分别对应Enviro_KingHamletPortrait、Enviro_Alter、Enviro_Grave_Elise；源SHA、准确旧值和行号均在既有ascension-dialogue-corrections.json中。三句已逐一核对原Assembly-CSharp.dll的GameDataGenerated实际ldstr。

## 码头回应纠正

此前答复将资源中的“No point. I know what's down there.”误当成当前玩家可触发内容。当前主游戏GameDataGenerated的所有字符串没有这一句；实际Invoke_Enviro_Locked_Docks在升格后只输出省略号，普通分支是“I have no reason to head to the docks right now.”。因此旧句在正常游玩及空城状态都不需要寻找，亦不是汉化遗漏了玩家能看到的一句。

level1的DoorMarker是过图门，不是独立可查看物件。先前只凭其名字和旧资源台词作清单，未核实实际编译结果，造成了错误。以后不能仅按同名资源场景判定当前运行内容；须回查GameDataGenerated。原方法及游戏程序集哈希见[编译来源核查](../../../runtime/evidence/empty-castle-compiled-source-2026-10-19.json)。该结论来自只读原IL，不称游戏现场验收。

删除码头后，有正文的特殊物件回应为5处：祭坛、老国王画像、哈姆雷特的箱子、画廊中的Beatrice画像、母亲坟墓。画像普通分支包含故乡和香鱼河流的诗句，连同内部Beatrice名指向海猫鸣泣之时彩蛋；很像的含义属于对升格后女主与操纵世界的魔女处境的解释，不是游戏明说的亲属关系。

## 验证

- 本轮仅3条目标变化，英文键、ID、顺序完全不变，无新增字。
- 72项真实XUnity递归消费者、17,069项实际字典解析通过。
- 40文件ZIP逐项一致，插件、字体、157条动态规则不变。
- 累计15条待安装；未进行剧情E2E、物理点击或像素验收，未访问存档。

[候选核验](../../../runtime/evidence/empty-castle-wording-verification-2026-10-19.json)
