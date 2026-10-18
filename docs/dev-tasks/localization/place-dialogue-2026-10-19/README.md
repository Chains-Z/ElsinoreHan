# 威登堡与主线对白跟进

状态：候选已验证、尚未安装。插件1.5.15，17,069词条、157规则、字体7,661。相对上一个候选新增38条修改；与此前22条有1条重合，合计59个词条待安装。

## 已处理

- Wittenberg按朱生豪《哈姆雷特》统一为威登堡，39条范围全覆盖：28条维滕贝格、4条威滕贝格改名，7条原本正确。包括人物介绍、日记、线索、普通对白、幽灵双层斜体及真实尾LF别名；英文Wittenburg原始拼写不改。
- plodding pace of fate的两个发言各有资源／编译源，4条统一为命运运转得太慢，才逼得他／我弟弟动了手。没有将plodding解释为残酷或不可抗拒；原文确有缓慢意。
- Guh两版按用户允许的选择统一为“啊——离我远点！离我们所有人远点！”。覆盖此前呃候选，历史对照仍保留阶段快照。

## 两段罕见对白的出处

`LaertesWitchAccuse` 位于升格杀戮路线的聚会指认分支；在`WITCH_WhoKnows`中，雷欧提斯须在场并认定女主是demon，且前面的克劳狄斯分支未抢先命中。这段并非普通结局正文。

`Witch_PoloniusDespair`是城墙上的观察事件，调度条件含demontripped、believes(polonius,demon)、counter_(erasedCount,6)。父亲崩溃，借用《李尔王》第五幕第三场李尔哀悼女儿的词句，随后自杀。女主仍在场，最后评论他临终已神志不清；不能把这段解释成父亲真在检查已死女主的呼吸。

## they及两个版本

Someone physically threatened me之后的They是指身份／性别未明的单个人，正常的单数they，并非英文错误。“那人”保留该不定指，不补性别，也不误加人数。

资源版指游戏剧情资源中的原始英文；运行版指编译或显示前加了斜体、替换破折号后的英文。例：资源`Guh-- Get away...`，运行`Guh—Get away...`；幽灵还会附加`<i>`。两种键用于覆盖真实查词路径，不意味着游戏原本有两套中文。同一意思被分开翻译后失配属于本补丁初稿及后续同步问题。两键可以保留，中文应复用审定结果；确实共享源但不同语境的情况另行处理。

## Playmaster称呼待定

真实角色介绍`p00574-c5811b545ad4`明确：Quince is the leader of a traveling troupe of players that occasionally perform at the castle. He writes and directs every play the group presents. 因而其表层身份是巡回剧团负责人兼编剧、导演，不足以认定为宫廷官职，也不能把master自动当作艺术造诣大师。

建议统一为班主，首次介绍可称戏班班主；截图句可为“彼得·昆斯？那个不起眼的乡下班主？可我不明白！”。这是结合游戏职责提出的译法，未找到其必须采用某个固定中译的证据。尚未修改全局称呼或线索标题。

## 验证

- 新109项消费者：旧候选实际复现94项不符，修正后全部通过；此前84项双源消费者通过。
- 137项受影响既有消费者通过。5份旧场景压力夹具的预期还遗漏更早校订，按同一真实场景与当前经治理对白原子重建，并断言英文输入逐字不变；未复制消费者actual充当预期。
- 19+4+7项治理／回归通过；708组成对变体及33条显式别名通过，无新未审差异／真实缺失／过期别名。
- 仅38条预期目标变化，无新增字符，插件／字体／规则不变；40文件候选ZIP逐项一致。未启动主游戏、未访问存档、未安装。

详见[核验证据](../../../../runtime/evidence/place-dialogue-verification-2026-10-19.json)。

## 来源

- [朱生豪《哈姆雷特》第一幕](https://www.dodobook.cc/novel/ha-mu-lei-te/18135)：威登堡。
- [牛津词典they](https://www.oxfordlearnersdictionaries.com/us/definition/english/they)：不知／不明说性别时指单个人。
- [剑桥词典plodding](https://dictionary.cambridge.org/us/dictionary/english/plodding)：缓慢、持续、沉闷。
- [Folger《李尔王》](https://www.folgerdigitaltexts.org/Lr/)：第五幕第三场镜面及哀悼词句。

## 本轮完整改前／改后

### 1．p00005-6f8b948dd1af

May 2, MDXXXV

Tonight my husband seemed distressed. At first I thought he was missing our son, gone to Wittenberg. But... as the night progressed, he seemed to grow old before my eyes. He seemed... broken, somehow. When the second course was served, he collapsed while raising a toast—ironically, a toast to our health. I took him on my shoulders and bore him out of the great hall and up to his bedroom myself.

As I lay him down in his bed, I noticed tears in his eyes. I tried to comfort him by kissing his forehead, but he pushed me away. "You will betray me," he rasped. "You will always betray me. Every time. You cannot do otherwise."

He collapsed into something like sleep, then, and would not answer my questions.

When I returned to the party, our guests were concerned, but Claudius stepped in to assure them. "Everything's all right!" he boomed, in his loudest, most regal voice. "Everyone—Drink more! Don't take your health for granted!"

Then he turned and offered me his hand. "Now. I think a dance with the Queen will restore some life to this party. Don't you?" he said, smiling at me. It was as though I were the only woman in the whole world. In all my time married to Hamlet, he never once looked at me like that.

That evening, when all the guests had gone to bed, I found myself outside my bedroom door, saying my goodnights to Claudius.

"I don't want to go to bed," I told him, laughing. "I want the night to continue. Stop the dawn!"

"As you wish, my Queen," he said, and kissed me.

I was surprised at first. And yet—I wasn't.

I kissed him back. He pulled my bedroom door shut behind him.

Surely I, too, deserve some happiness in this world that has been so cruel to me.

Don't I?

改前：MDXXXV年5月2日

今晚，丈夫似乎心神不宁。起初，我以为他在想念去了维滕贝格的儿子。但……随着夜色渐深，他仿佛在我眼前衰老了。他看起来……像是被什么击垮了。第二道菜端上来时，他正举杯祝酒，却倒了下去——讽刺的是，他祝的正是我们身体安康。我把他扛在肩上，亲自将他带出大厅，送上楼送进他的卧室。

把他放到床上时，我发现他眼里有泪。我吻了吻他的额头，想安慰他，他却推开了我。“你会背叛我，”他声音嘶哑地说，“你永远都会背叛我。每一次。你做不到别的。”

随后，他陷入了像是睡眠的状态，不再回答我的问题。

我回到宴会上时，宾客们都很担心，克劳狄斯却站出来安抚他们。“一切都好！”他用最洪亮、最有王者威严的声音说道，“各位——再多喝些！别把身体安康当成理所当然！”

接着，他转身向我伸出手。“来吧。我想，与王后共舞一曲，会让这场宴会重新热闹起来。你说呢？”他说着，朝我微笑。仿佛我是全世界唯一的女人。嫁给哈姆雷特这么久，他从未这样看过我，哪怕一次。

那晚，宾客们都去睡了，我站在自己的卧室门外，正向克劳狄斯道晚安。

“我不想睡，”我笑着对他说，“我想让这一夜继续下去。别让天亮！”

“遵命，我的王后。”他说，然后吻了我。

起初我很惊讶。然而——我又并不惊讶。

我回吻了他。他随手关上了身后的卧室门。

这个世界对我如此残酷，我当然也该得到一些幸福。

难道不是吗？

改后：MDXXXV年5月2日

今晚，丈夫似乎心神不宁。起初，我以为他在想念去了威登堡的儿子。但……随着夜色渐深，他仿佛在我眼前衰老了。他看起来……像是被什么击垮了。第二道菜端上来时，他正举杯祝酒，却倒了下去——讽刺的是，他祝的正是我们身体安康。我把他扛在肩上，亲自将他带出大厅，送上楼送进他的卧室。

把他放到床上时，我发现他眼里有泪。我吻了吻他的额头，想安慰他，他却推开了我。“你会背叛我，”他声音嘶哑地说，“你永远都会背叛我。每一次。你做不到别的。”

随后，他陷入了像是睡眠的状态，不再回答我的问题。

我回到宴会上时，宾客们都很担心，克劳狄斯却站出来安抚他们。“一切都好！”他用最洪亮、最有王者威严的声音说道，“各位——再多喝些！别把身体安康当成理所当然！”

接着，他转身向我伸出手。“来吧。我想，与王后共舞一曲，会让这场宴会重新热闹起来。你说呢？”他说着，朝我微笑。仿佛我是全世界唯一的女人。嫁给哈姆雷特这么久，他从未这样看过我，哪怕一次。

那晚，宾客们都去睡了，我站在自己的卧室门外，正向克劳狄斯道晚安。

“我不想睡，”我笑着对他说，“我想让这一夜继续下去。别让天亮！”

“遵命，我的王后。”他说，然后吻了我。

起初我很惊讶。然而——我又并不惊讶。

我回吻了他。他随手关上了身后的卧室门。

这个世界对我如此残酷，我当然也该得到一些幸福。

难道不是吗？

### 2．p00009-9e2ba93d2278

June 6, MDXXXV

Ophelia will not even look at me. My love for her means nothing now. And in the great hall, they rejoice my uncle's crowning, my father's proud form but a distant memory. If my uncle does not allow me to return to Wittenberg soon, I fear I will well and truly perish.

 August 8

That <i>thing</i> was not my father. It can't be. My father lies buried.

But if it wasn't my father... what devil or evil spirit was it? Am I truly losing my mind? Was it real? Can I be certain it wasn't just a horrid dream? No, the others saw it too... even if they won't speak to me of it.

My uncle cannot be trusted. Devils disregarded, there is yet something evil in him. I found the literature which Bernardo mentioned, tucked away in the gallery downstairs... it only confirms my suspicions. And yet... something in me keeps me from acting on it. What has stolen my courage?

改前：MDXXXV年6月6日

奥菲莉娅连看都不愿看我一眼。我对她的爱，如今已毫无意义。大厅里，他们欢庆着叔父加冕，父亲那威严的身影却已成了遥远的记忆。如果叔父不尽快准许我回维滕贝格，我怕自己真的会死去。

 8月8日

那个<i>东西</i>不是我的父亲。不可能是。我的父亲已埋在地下。

但如果那不是父亲……那又是什么魔鬼或邪灵？我真的正在发疯吗？那是真的吗？我能确定那不只是一场可怕的梦吗？不，其他人也看见了……即使他们不愿和我谈起它。

叔父不可信。即便不去管那些魔鬼，他身上也仍有邪恶的东西。我找到了贝尔纳多提过的文字，藏在楼下的画廊里……它只是进一步证实了我的怀疑。然而……我心里有什么东西，让我迟迟无法据此采取行动。是什么夺走了我的勇气？

改后：MDXXXV年6月6日

奥菲莉娅连看都不愿看我一眼。我对她的爱，如今已毫无意义。大厅里，他们欢庆着叔父加冕，父亲那威严的身影却已成了遥远的记忆。如果叔父不尽快准许我回威登堡，我怕自己真的会死去。

 8月8日

那个<i>东西</i>不是我的父亲。不可能是。我的父亲已埋在地下。

但如果那不是父亲……那又是什么魔鬼或邪灵？我真的正在发疯吗？那是真的吗？我能确定那不只是一场可怕的梦吗？不，其他人也看见了……即使他们不愿和我谈起它。

叔父不可信。即便不去管那些魔鬼，他身上也仍有邪恶的东西。我找到了贝尔纳多提过的文字，藏在楼下的画廊里……它只是进一步证实了我的怀疑。然而……我心里有什么东西，让我迟迟无法据此采取行动。是什么夺走了我的勇气？

### 3．p00045-449ed994c76f

Horatio is Hamlet's schoolmate from Wittenberg. From the look of him he can't be Danish, but I've never known his origin.

He served as a soldier in the last war alongside Bernardo, and from the way he carries himself he must be of noble birth, though exactly how I'm not sure. He's well-educated and eloquent, and always has something interesting to say.

改前：霍拉旭是哈姆雷特在维滕贝格的同学。看他的相貌，他不可能是丹麦人，但我从来不知道他来自哪里。

上一次战争中，他曾和贝尔纳多一起当兵。从他的举止来看，他一定出身贵族，至于具体是什么来头，我不清楚。他学识丰富，口才很好，说的话总是很有趣。

改后：霍拉旭是哈姆雷特在威登堡的同学。看他的相貌，他不可能是丹麦人，但我从来不知道他来自哪里。

上一次战争中，他曾和贝尔纳多一起当兵。从他的举止来看，他一定出身贵族，至于具体是什么来头，我不清楚。他学识丰富，口才很好，说的话总是很有趣。

### 4．p00545-eda428fdc315

Hamlet and I were together for two years, in secret. In that time, he was... different. Happier. He had a sense of humor then. Neither of us had ever loved another before, but he treated me with respect and an unfailing kindness. He went away to Wittenberg for University, and then his father passed, and he came back a changed person. These days, it's hard to look at him; all I see is the person he used to be.

改前：哈姆雷特和我曾秘密交往了两年。那时候，他……不一样。更快乐。那时的他还有幽默感。我们此前都没有爱过别人，但他尊重我，对我的温柔体贴也从未变过。他去了维滕贝格上大学，后来父亲去世了，他回来时就变了个人。如今，我很难面对他；看着他，我眼里只有他过去的样子。

改后：哈姆雷特和我曾秘密交往了两年。那时候，他……不一样。更快乐。那时的他还有幽默感。我们此前都没有爱过别人，但他尊重我，对我的温柔体贴也从未变过。他去了威登堡上大学，后来父亲去世了，他回来时就变了个人。如今，我很难面对他；看着他，我眼里只有他过去的样子。

### 5．p00560-edb527da0d89

Horatio was born in India, the son of a spice merchant who sailed between Venice and Calicut. He never knew his mother. He was raised as a Venetian, and at some point made his way to Denmark, which is where he entered King Hamlet's employ as a soldier. He's remained here ever since, barring the time he was with Hamlet at Wittenberg.

改前：霍拉旭出生于印度，父亲是往返于威尼斯和卡利卡特的香料商人。他从未认识自己的母亲。他作为威尼斯人长大，后来在某个时候辗转来到丹麦，在这里受雇于哈姆雷特国王，成为一名士兵。此后他一直留在这里，只有陪哈姆雷特去维滕贝格的那段时间除外。

改后：霍拉旭出生于印度，父亲是往返于威尼斯和卡利卡特的香料商人。他从未认识自己的母亲。他作为威尼斯人长大，后来在某个时候辗转来到丹麦，在这里受雇于哈姆雷特国王，成为一名士兵。此后他一直留在这里，只有陪哈姆雷特去威登堡的那段时间除外。

### 6．p00562-318b3c3eed25

Hamlet and Horatio departed for Wittenberg together, it turns out. King Hamlet sent Horatio to watch over Hamlet while Hamlet was in school, since Horatio was older and calmer than Hamlet. But Horatio and Hamlet became close, and Horatio told Rosencrantz that he's been in love with Hamlet ever since.

改前：原来，哈姆雷特和霍拉旭是一起去维滕贝格的。霍拉旭比哈姆雷特年长，也更沉稳，所以哈姆雷特国王派他在哈姆雷特求学期间照看王子。不过，霍拉旭和哈姆雷特变得亲密起来，霍拉旭告诉罗森克兰兹，从那时起，他就一直爱着哈姆雷特。

改后：原来，哈姆雷特和霍拉旭是一起去威登堡的。霍拉旭比哈姆雷特年长，也更沉稳，所以哈姆雷特国王派他在哈姆雷特求学期间照看王子。不过，霍拉旭和哈姆雷特变得亲密起来，霍拉旭告诉罗森克兰兹，从那时起，他就一直爱着哈姆雷特。

### 7．p01252-aef489d73fbf

When he returned from Wittenberg, I thought... well.

改前：他从维滕贝格回来时，我还以为……唉。

改后：他从威登堡回来时，我还以为……唉。

### 8．p01388-dbe6b5bbbf91

Back to university at Wittenberg, you mean?

改前：您是说，送他回维滕贝格的大学？

改后：您是说，送他回威登堡的大学？

### 9．p01389-c8365c30cfd5

Wittenberg? No, no. The prince deserves to see new sights, don't you think?

改前：维滕贝格？不，不。王子也该见识些新风景，你说呢？

改后：威登堡？不，不。王子也该见识些新风景，你说呢？

### 10．p04388-f1b1f78bd51d

There's not much to tell, my lady. I'm but a poor footsoldier. Then I followed Hamlet to Wittenberg, for a time.

改前：没什么可说的，王后。我不过是个穷步兵。后来我跟着哈姆雷特去了维滕贝格，待过一段时间。

改后：没什么可说的，王后。我不过是个穷步兵。后来我跟着哈姆雷特去了威登堡，待过一段时间。

### 11．p04823-8f8fe5c1c53f

Might it not be in the woods by the pond? I seem to recall us going out there the last time you were home from Wittenberg.

改前：会不会在池塘边的树林里？我好像记得，上次你从维滕贝格回家时，我们去过那里。

改后：会不会在池塘边的树林里？我好像记得，上次你从威登堡回家时，我们去过那里。

### 12．p05088-d8c8ac7aeb25

<i>Do not hate him, my love. His hand was forced by the plodding pace of fate.</i>

改前：<i>不要恨他，我的爱人。是命运沉缓的步伐逼他出手。</i>

改后：<i>不要恨他，我的爱人。命运运转得太慢，才逼得他动了手。</i>

### 13．p05098-30aca2c52c05

<i>And do not hate Claudius, my good man. My brother's hand was forced by the plodding pace of fate.</i>

改前：<i>也不要恨克劳狄斯，我的好臣子。是命运沉缓的步伐逼我弟弟出手。</i>

改后：<i>也不要恨克劳狄斯，我的好伙计。命运运转得太慢，才逼得我弟弟动了手。</i>

### 14．p05244-f4809e7ccf17

Say, Ophelia. I don't think I want to go back to Wittenberg, where we all went to school.

改前：对了，奥菲莉娅。我想我不愿意再回维滕贝格了，就是我们一起上学的地方。

改后：对了，奥菲莉娅。我想我不愿意再回威登堡了，就是我们一起上学的地方。

### 15．p05349-ace1b99d76ad

Initially, I persuaded Rosie to come to Elsinore in part because... of what happened between us in Wittenberg.

改前：起初，我劝萝茜来埃尔西诺，部分原因是……我们在维滕贝格发生的那些事。

改后：起初，我劝萝茜来埃尔西诺，部分原因是……我们在威登堡发生的那些事。

### 16．p05365-7dcc322c9fbb

Everything that happened between us in Wittenberg seemed...

改前：我们在维滕贝格发生的一切，似乎……

改后：我们在威登堡发生的一切，似乎……

### 17．p05394-4a4c780cc262

At Wittenberg, women who looked like Ophelia and me were <i>afraid</i> to refuse you. You're a Prince.

改前：在维滕贝格，长得像奥菲莉娅和我这样的女人，<i>不敢</i>拒绝你。你是王子。

改后：在威登堡，长得像奥菲莉娅和我这样的女人，<i>不敢</i>拒绝你。你是王子。

### 18．p07093-2c59fd99346c

When I was with Hamlet at Wittenburg, there was a game some of the students liked to play.

改前：我和哈姆雷特在维滕贝格的时候，有些学生很喜欢玩一个游戏。

改后：我和哈姆雷特在威登堡的时候，有些学生很喜欢玩一个游戏。

### 19．p07120-cfbdbb807807

You just <i>came</i> from Wittenberg. I've no doubt Martin Luther is bar crawling, basking in his unpopularity there still... for <i>now.</i>

改前：你刚从维滕贝格<i>回来</i>。我毫不怀疑马丁·路德还在那里一家酒馆接一家地喝，享受着自己不受欢迎的名声……<i>暂时如此。</i>

改后：你刚从威登堡<i>回来</i>。我毫不怀疑马丁·路德还在那里一家酒馆接一家地喝，享受着自己不受欢迎的名声……<i>暂时如此。</i>

### 20．p08334-5170d58145fc

They want to return to Wittenberg, and for me to join them.

改前：她们想回维滕贝格，也想让我一起去。

改后：她们想回威登堡，也想让我一起去。

### 21．p08335-a5a5488ca048

<i>Wittenberg?</i> At a time like this?

改前：<i>维滕贝格？</i>在这种时候？

改后：<i>威登堡？</i>在这种时候？

### 22．p08401-7981c7193ae0

When I was at Wittenberg I was surrounded by men and women in the midst of a great rebirth. Arts, culture, knowledge—it was fantastic.

改前：在维滕贝格时，我身边的男男女女都置身于一场伟大的复兴之中。艺术、文化、知识——那一切都太精彩了。

改后：在威登堡时，我身边的男男女女都置身于一场伟大的复兴之中。艺术、文化、知识——那一切都太精彩了。

### 23．p08683-5da94e727d63

Come back to Wittenberg with us. Let some other fool run the country!

改前：跟我们回维滕贝格吧。让别的蠢货去治理这个国家！

改后：跟我们回威登堡吧。让别的蠢货去治理这个国家！

### 24．p10314-7bfd479657ea

Hamlet was to be educated at Wittenberg soon. But Hamlet's father was worried about him.

改前：哈姆雷特不久就要去威滕贝格求学了。但他的父亲很不放心。

改后：哈姆雷特不久就要去威登堡求学了。但他的父亲很不放心。

### 25．p10321-9ee3e6225180

So King Hamlet sent you along to Wittenberg to watch over Hamlet. Is that it?

改前：所以哈姆雷特国王派你一起去威滕贝格，照看哈姆雷特。是这样吗？

改后：所以哈姆雷特国王派你一起去威登堡，照看哈姆雷特。是这样吗？

### 26．p10329-b80d64c16a58

Horatio, you ought to know me better than that. How many of <i>my</i> lady loves did you meet at Wittenberg?

改前：霍拉旭，你应该更了解我才对。在威滕贝格，你见过多少位<i>我的</i>女情人？

改后：霍拉旭，你应该更了解我才对。在威登堡，你见过多少位<i>我的</i>女情人？

### 27．p10378-6ef6a93be10a

Do you remember that night in Wittenberg, during that first year?

改前：你还记得在威滕贝格第一年时的那个晚上吗？

改后：你还记得在威登堡第一年时的那个晚上吗？

### 28．p10596-dda136641ec4

And I want to return to Wittenberg, because—I agree—these Danish walls are absolutely miserable.

改前：而我想回维滕贝格，因为——我也这么觉得——丹麦这城墙里的日子实在难熬。

改后：而我想回威登堡，因为——我也这么觉得——丹麦这城墙里的日子实在难熬。

### 29．p10854-27dc32e1cc88

I'll kill him. I'll tear him down until he regrets leaving Wittenberg.

改前：我要杀了他。我要把他彻底打垮，让他后悔离开维滕贝格。

改后：我要杀了他。我要把他彻底打垮，让他后悔离开威登堡。

### 30．p13828-d679f808f9c8

Guh-- Get away from me! From all of us!

改前：呃——离我远点！离我们所有人远点！

改后：啊——离我远点！离我们所有人远点！

### 31．p14268-87edf0f2c28e

But, you know, before they went to Wittenberg, the two of them didn't get along very well at all. It's wonderful to see things have changed.

改前：不过，你知道吗，在去维滕贝格之前，他们两个相处得很不好。看到他们如今变了，真让人高兴。

改后：不过，你知道吗，在去威登堡之前，他们两个相处得很不好。看到他们如今变了，真让人高兴。

### 32．p14294-9d2b79617dd0

Not much. Merely that Hamlet went away to Wittenberg with Horatio, and when the both of them returned, Rosencrantz and Guildenstern were in tow.

改前：不多。只知道哈姆雷特和霍拉旭一起去了维滕贝格，等他们两个回来时，罗森克兰兹和吉尔登斯吞也跟着来了。

改后：不多。只知道哈姆雷特和霍拉旭一起去了威登堡，等他们两个回来时，罗森克兰兹和吉尔登斯吞也跟着来了。

### 33．p14305-56aa1b41ed6b

The King denied Hamlet's request to return to Wittenberg, on the grounds that the Queen needs him here.

改前：国王拒绝了哈姆雷特返回维滕贝格的请求，理由是王后需要他留在这里。

改后：国王拒绝了哈姆雷特返回威登堡的请求，理由是王后需要他留在这里。

### 34．p15017-6911e29b5742

He came from Wittenberg to see his father before the elder Hamlet passed of plague.

改前：在老哈姆雷特因瘟疫去世之前，他从维滕贝格赶回来看望父亲。

改后：在老哈姆雷特因瘟疫去世之前，他从威登堡赶回来看望父亲。

### 35．p15134-5589bc61bed4

She needs some time to mother him here. If he goes to Wittenberg, what then? She'll be a worried tangle for the whole year.

改前：她需要一些时间，让他留在这里，好好照顾他。要是他去了维滕贝格，那怎么办？她会一整年都忧心忡忡。

改后：她需要一些时间，让他留在这里，好好照顾他。要是他去了威登堡，那怎么办？她会一整年都忧心忡忡。

### 36．a00224-57a37b78cad6

Guh—Get away from me! From all of us!

改前：呃——离我远点！离我们所有人远点！

改后：啊——离我远点！离我们所有人远点！

### 37．a00456-4ef20fb06483

<i><i>Do not hate him, my love. His hand was forced by the plodding pace of fate.</i></i>

改前：<i><i>不要恨他，我的爱人。是命运迟缓的脚步逼他动了手。</i></i>

改后：<i><i>不要恨他，我的爱人。命运运转得太慢，才逼得他动了手。</i></i>

### 38．a00460-500d1e0bebd8

<i><i>And do not hate Claudius, my good man. My brother's hand was forced by the plodding pace of fate.</i></i>

改前：<i><i>也不要恨克劳狄斯，我的好伙计。是命运迟缓的脚步逼我弟弟动了手。</i></i>

改后：<i><i>也不要恨克劳狄斯，我的好伙计。命运运转得太慢，才逼得我弟弟动了手。</i></i>
