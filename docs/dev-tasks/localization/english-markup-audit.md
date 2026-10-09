本项目原文中的斜体和粗体不能归结为一条稳定的“粗体比斜体强调更强”规则。斜体确实常标记对白重读，但同时用于角色声音、唱词、引用、作品名、外来语及日志舞台说明；粗体也兼用于正文强调、任务线索、姓名、栏目与标题。用户已选择中文斜体对应原文斜体，本次只读审计支持保留这些区别，不修改译文或显示样式。

中文可以采用倾斜字形作为版式选择；“传统中文正文不普遍采用西文式斜体”不能推成“汉字禁止斜体”，也不能推成“译著都应直接保留斜体”。[Adobe 的中日韩斜变体文档](https://helpx.adobe.com/cn/indesign/desktop/language-and-proofing/chinese-japanese-and-korean/apply-shatai-to-text.html)明确支持对缺少斜体字体变体的 CJK 文字应用倾斜字符样式。这是实际排版能力的证据，不是所有出版物的体例规范。本项目按用户偏好保留 i/b，不把该选择宣称为所有中文出版物的统一规范。软件合成倾斜和专门设计的西文 Italic 字形也不是同一种字体设计；是否好读须看实际字号和字形。

英文的一般用途已核查：[北京师范大学出版科学研究院](https://pub.bnu.edu.cn/jzyg1/9b35bfc0318649c5b7580f08f1a4be6a.html)列举斜体用于强调、作品名和部分外来语；[Chicago 小说用法说明](https://www.chicagomanualofstyle.org/qanda/data/faq/topics/ItalicsandQuotationMarks/faq0010.html)说明它也可以区分内心话等不同话语来源；[Chicago 强调问答](https://www.chicagomanualofstyle.org/qanda/data/faq/topics/ItalicsandQuotationMarks/faq0004.html)指出粗体更醒目，是否适合取决于所需效果及出版社体例。这些资料支持“用途不限于强调”，不支持本游戏存在固定的粗斜体强弱等级。书名的中文书名号、着重号或另换字体均须结合语义使用；它们不是必须批量取代原文 i 的理由。

全量频次来自合并词表的 16,841 条不同英文源串。统计是源串内的标记次数，不是游玩时出现次数；资源源文、程序集变体及复用别名均按各自精确源串计算。动态生成的完整日志封套没有额外加到这个分母。输入哈希、24 个原句样本、原始跨度、scene/speaker/cue 和生成器证据见 [english-markup-audit.json](../../../analysis/ui-audit/english-markup-audit.json)。

| 标记 | 含开/闭标记的源条目 | 开标签 | 同标签配对跨度 | 整条源串被包裹 |
| --- | ---: | ---: | ---: | ---: |
| `<i>` | 2,037 | 2,157 | 2,151 | 529 |
| `<b>` | 249 | 265 | 264 | 9 |

计数使用嵌套栈；只有跨度从源串首字符覆盖到末字符才计为整条包裹，多个局部斜体不会误算整句。两种标记都有的源串数另存 JSON。配对跨度按同标签栈计算，不代表原始富文本全都嵌套合法。源中有 `<b>still</i>`、缺失关闭标签和交叉关闭等异常，已原样记录，未修正。

| 用途与判断依据 | 真实源句 | ID |
| --- | --- | --- |
| 局部重读，程度词是焦点 | `...sometimes a little <i>too</i> attentive.` | `p00037-11bb9e7b46b6` |
| 内心话由括号区分，内部另有强调 | `(I can <b>change it.</b> I <i>have</i> to.)` | `p01137-b79a56189792` |
| 内心话也可完全没有 i/b | `(This is so strange. Did history itself change?)` | `p00389-7482aa3b9349` |
| 整句 i 也能是当面对话；Laertes，angry cue | `<i>What did you call her?</i>` | `p03311-976dce3319e4` |
| 幽灵角色声音；编译器还会统一加外层 i | `<i>Patience, Hamlet.</i>` | `p01729-c502bfd17a6c` |
| 歌词；OthelloSinging 场景 | `<i>The poor soul sat singing by a tree, sing all a green willow...</i>` | `p07025-6a1fc8b2122f` |
| 引述命令文件；HamletFindNote 场景 | `<i>I've entrusted these orders to two loyal servants, Rosencrantz and Guildenstern, to ensure that...</i>` | `p05328-0165632469f0` |
| 作品名；BookPlay 场景及 Title_Merchant cue | `<i>The Mirthful Merchant.</i>` | `p07508-8b6b5aec2f17` |
| 同句中 i 的用途也不同：外来语及重读 | `Oh, Ophelia. <i>Mon dieu.</i> I've just been struck by <i>genius.</i>` | `p11778-0309b0006984` |
| 脚本中的舞台式文字；资源类型仍是 Dialogue | `<i>Exit HAMLET.</i>` | `p13702-b00e70711b34` |
| 局部语气可解释为加重，但不足以构成全局规则 | `<i>Laps.</i> <b>Now.</b> Put the cards down and get running.` | `p02617-de144e56a379` |
| b 内仍可有 i：调查命题与词级重读是两维用途 | `...<b>I must find out if my mother knew of this. I <i>have</i> to know if she was complicit, too.</b>` | `p11655-30cc338e46f1` |
| 正文 b 有情绪重读用途 | `People are <b>dead</b> outside.` | `p00493-fc87d3d444f2` |
| 系统通知中的姓名 b，不表示声音更强 | `<b>Ophelia</b> acquires the information "%s."` | `ui-35f959311ff432c1` |
| 系统条目名与栏目 b | `Ophelia learns more about <b>%s</b>. The entry will be updated in the <b>Journal</b>.` | `ui-2c128aff02f4ecc1` |

生成器证据尤其重要。`GameRunner.CompileContent` 的 `IL_0257` 为 `fix-ghost-lines`，`IL_025c` 为 `ghost`；随后执行 `CompilerPasses.italicizeAllDialogueOf`。该 Pass 对匹配角色的完整对白使用 `<i>%s</i>`，不会去掉正文已有的 i/b。因此整句幽灵斜体不能当作内心话，嵌套的 i 也不证明作者希望两倍倾斜。

`HistoryTracker.formatEntry` 则分别生成 `<b>{speaker}:</b> <indent=16%>{Dialogue.Text}`，以及舞台说明/提示的 `<i>...</i>` 外层。这些 i/b 是日志结构样式，和 `Dialogue.Text` 内部的作者标记分属不同层次。上表的 `Exit HAMLET` 是脚本对白中的真实字面量，也不能据标签直接与动态 `LogEntry.Stage` 合并分类。

中文对应建议维持当前用户选择：作者局部 i 保留 i，作者 b 保留 b，角色及日志封套保留各自结构；书名、引文、内心话需要结合具体语义决定中文标点和版式，不能只靠标签批量判断。源标记错误另立精确修订，不用全局替换掩盖。尚未对全量跨度逐条语义分类，上表仅是经上下文核对的代表证据；此文件没有用英文书名斜体证明汉字斜体规范，也没有宣称游戏渲染验收通过。
