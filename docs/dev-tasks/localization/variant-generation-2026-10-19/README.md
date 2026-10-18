# 格式变体改为单一中文来源

后续称号决定：已恢复“戏剧大师”，三处轻蔑身份的对白使用“艺人”，详见[后续记录](../playmaster-tone-2026-10-19.md)。本页以下称号与数量为该阶段快照。

状态：离线验证完成，候选包已生成，尚未安装。插件仍为1.5.15，17,069词条、157规则和7,661字形不变。相对上一候选528个目标变化，连同此前60条合计588条待安装。

## 实现结果

- 889份规范译文自动生成1,784个现有英文查找键，895条格式关系来自真实对白、资源编译和显式运行别名。中文不再分别维护资源版、运行版。
- 708组真实成对对白全部纳入管理：707组一致，1组保留语境例外。`I do.`裸源为“是的。”，幽灵为“是的，我也一样。”，不强行合并不同含义。
- 迁移以现有已审运行译文为准，统一495个旧变体的措辞或强调位置；迁移本身没有改写实际编译对白的译文。旧修订文件和差异审查保留历史快照。
- 用户最终确认Playmaster为“戏班班主”，33处称呼、线索和运行别名同步。与菲劳斯特莱特的Master of the Revels（掌戏乐之官）分开；[Folger人物表](https://www.folgerdigitaltexts.org/MND/)中昆斯为Peter Quince, carpenter，并无相同的Playmaster职衔。
- 宴席两句按最新反馈修正，详见下表。共享`Of course.`仍为“当然。”，避免其他人物确认事实时被改为“好的。”。

| 英文 | 改前 | 改后 |
| --- | --- | --- |
| Come, Ophelia. Let me show you to your seat. Shall we dine? | 来，奥菲莉娅。我带你入座。我们用餐吧？ | 来，奥菲莉娅。我带你入座。那我们开始用餐吧？ |
| To some, our relationship has been known a long time. To others, it may be—er—more of a surprise. | 有些人早就知道我们的关系。对另一些人来说，这可能——呃——更像是个意外。 | 有些人早就知道我们的关系。对另一些人来说，这可能——呃——会让他们很意外。 |

`Shall we dine?`作为礼貌提议，不改成询问女主是否愿意与霍拉旭单独约餐，也不增加请求她许可的意味。用户否定的“愿意一起用餐吗”“我们可以开始用餐了吗”均未进入最终候选。

## 维护入口

已绑定句子日后只修改[规范译文](../../../../translation/supplemental/canonical-variant-translations.json)的`target`，记录审定依据和来源；不要修改生成的`translations.json`，不要回写旧校订层。导出器会按[格式合同](../../../../translation/supplemental/generated-variant-bindings.json)同步全部已知变体。未绑定句子仍使用原有准确旧值校订流程。

新增格式关系须核对真实源、原始词条ID、源哈希、准确迁移旧译及来源；新增真实成对对白未登记时，审查命令失败，不静默放过。初始化迁移脚本拒绝覆盖已有规范译文，日常导出不重新选取中文。

```powershell
python tools/translation/export_sol_full.py
python tools/translation/audit_source_variants.py
python tools/translation/prepare_generated_variant_followup.py
python -m unittest discover -s tools/translation -p 'test_*.py'
& tools/translation/verify-recursive-ui.ps1 -TestsPath translation/supplemental/generated-variant-tests.json
& tools/patch/package-full.ps1 -PendingInstall
```

进一步说明见[实现](implementation.md)、[验证](verification.md)和[候选证据](../../../../runtime/evidence/variant-generation-verification-2026-10-19.json)。未操作主游戏进程或存档，也未宣称游戏画面或完整剧情E2E通过。
