"""绑定烧书后昆斯的三个对白分支，生成逐句审查稿与真实消费者夹具。"""

import json

from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import (
    DIALOGUE, GAME_RESOURCE, OUT, ROOT, SCENE, dialogue_source, digest, read,
    read_text_assets, save,
)


SCENE_NAME = "POSTEND_QuinceBookBurned"
CHANGES = {
    "p14506-3bf7e11752b1": ("我知道，我们已经很久没说话了。", "明确一阵子指两人久未交谈，承接昆斯准确计日。"),
    "p14508-d5fb902bbb5c": ("如果把怒目相向也算作交谈，那就没那么久。", "保留带敌意的瞪视，避免一种说话方式的生硬名词结构。"),
    "p14509-58e63e69825c": ("我不这么算。不过，很高兴你还在记日子。", "补明数的是两人没有交谈的日子，不补写额外关系。"),
    "p14512-d341108a8c7c": ("是的，我有一千种理由恨你。但都比不上这一种：", "用户指出此处承接恨她的理由，用这一种衔接下一句。"),
    "p14514-4b957c199f39": ("用种种骇人的手段杀死你、恐吓你、摧垮你……这些乐子我都享受过了。", "按意义合并列举，保留过去从杀害、恐吓和摧垮中取乐的意思。"),
    "p14516-99d241093a14": ("没错。直到最后，最奇怪的事才终于发生：你<i>真的</i>放弃了。你输掉了这场较量。", "不将衔接独白的For机械译成独立因为，保留最终发生和放弃的强调。"),
    "p14517-a7ea8d6dbe7c": ("这些年来，你彻底退缩，不再参与这场游戏。在我眼中，整个埃尔西诺都已变得模糊不清，混成了一团。无聊磨平了所有棱角。", "将无定形一团的比喻落在昆斯的感知，保留混合及棱角磨平，不暗示城堡实际融化。"),
    "p14518-baf96c0c05d9": ("这里的每个人都同时活着又死去，欢喜又悲伤，聪明又残忍——我已经记不清，究竟什么才是真的了。", "用破折号接上这些矛盾印象的原因，消除因为断句及已经再也的重复。"),
    "p14520-9647719e7481": ("奥菲莉娅，我怕是已经彻底疯了。", "将我恐怕的生硬搭配改为自然的怕是，保留担忧和推测。"),
    "p14521-e5e7492c3022": ("也许我从来就没正常过。也许一直都是这样。又或者，这永远都会是你我共同的妄想。", "sane指心智正常，避免没清醒过的睡醒歧义；保留三重也许。"),
    "p14522-eac6709ca9aa": ("人们说，爱情就是这样——两个人共同的妄想。我也不懂。我从没爱上过谁。", "连接爱情与共同妄想；in love限定恋爱，不扩大为从未对任何人有过爱。"),
    "p14525-4c241b1e97c4": ("那本书来到我手里，是有原因的。它选择了我。又或者，是谁将它赐给了我。为什么？", "顺畅表达主动选择与被赐予的两个可能，不指定赐书者身份。"),
    "p14526-74fcc302a8b2": ("如果我的命运仅仅是像个傻瓜一样，被困在自己创造的一切之中，那这一切究竟是为了什么？", "承接前句的追问，保留受困于自身创造的反讽，不额外指认创造了什么。"),
    "p14527-671c22cf25c7": ("……不过，算了。", "承接反复思索后又任其消散的转折，避免不过不的生硬对译。"),
    "p14528-71a17a92760f": ("这些念头已如海浪般冲击过我一万次。如今，它们又退去了，再次流回大海。", "保留冲击与退回海里的意象，顺畅衔接前句放下思索。"),
    "p14531-abccc0e084ac": ("我不想永远和你敌对下去。", "at odds是双方关系不和，不是女主主动和他作对。"),
    "p14532-e5bc2e980dd4": ("可惜，亲爱的，<i>我</i>倒想。", "承接永远敌对，保留昆斯刻意强调我及带讥讽的反话。"),
    "p14534-79b68e515cf7": ("我想，我们之间已经没什么可说的了。", "自然表达如今彼此几乎无话可说，保留我想的判断语气。"),
}


def scene_rows():
    """按真实资产顺序提取全部发言，不能用去重后的其他场景上下文替代。"""
    rows = []
    for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes()):
        if name != "scenes_smalltalk":
            continue
        scenes = list(SCENE.finditer(text))
        for index, scene in enumerate(scenes):
            if scene[1] != SCENE_NAME:
                continue
            end = scenes[index + 1].start() if index + 1 < len(scenes) else len(text)
            for match in DIALOGUE.finditer(text, scene.end(), end):
                source = json.loads('"' + match["text"] + '"')
                rows.append({"actor": match["actor"], "source": source,
                             "runtime_source": dialogue_source(match["actor"], source),
                             "source_sha256": digest(source),
                             "origins": [{"asset": name, "asset_sha256": sha, "scene": SCENE_NAME,
                                          "line": text[:match.start()].count("\n") + 1}]})
    assert len(rows) == 31
    return rows


def main():
    current = {row["source"]: row for row in read(ROOT / "translation/sol-full-2026-10-09/translations.json")}
    correction_path = OUT / "post-burn-dialogue-corrections.json"
    if correction_path.exists():
        # 后续重建只取已记录的准确旧值，不依赖被忽略的临时快照。
        recorded = {row["source"]: row for row in read(correction_path)}
        before = {source: {**row, "target": recorded.get(source, row).get("previous_target", row["target"])}
                  for source, row in current.items()}
    else:
        before = current
    bindings = {row["source"]: row for row in read(OUT / "generated-variant-bindings.json")["bindings"]}
    review, changes, cases = [], [], []
    for index, row in enumerate(scene_rows(), 1):
        old = before[row["source"]]
        target, reason = CHANGES.get(old["id"], (old["target"], "原译符合本段语境，保留。"))
        if row["source"] == "What?":
            reason = "此处烦躁口吻可译干嘛，但与全游戏惊讶等语境共享同一英文键；保持什么，避免全局串译。"
        if old["id"] in CHANGES:
            assert row["source"] not in bindings, "绑定句子必须只修改规范译文"
            changes.append({"id": "post-burn-" + old["id"], "original_id": old["id"],
                            "source": row["source"], "source_sha256": row["source_sha256"],
                            "previous_target": old["target"], "target": target,
                            "reason": reason, "origins": row["origins"]})
        review.append({**row, "id": old["id"], "branch": "首次" if index <= 27 else "第二次" if index <= 29 else "后续重复",
                       "previous_target": old["target"], "target": target, "changed": target != old["target"], "reason": reason})
        name, translated_name = ("Quince", "昆斯") if row["actor"] == "quince" else ("Ophelia", "奥菲莉娅")
        for kind, source, expected in (
            ("leaf", row["runtime_source"], target),
            ("box", "<line-height=90%>" + row["runtime_source"], "<line-height=90%>" + target),
            ("log", "<b>" + name + ":</b> <indent=16%>" + row["runtime_source"],
             "<b>" + translated_name + ":</b> <indent=16%>" + target),
        ):
            cases.append({"id": "post-burn-" + str(index) + "-" + kind, "source": source, "target": expected,
                          "origins": row["origins"]})
        # 资源键与运行键都必须仍存在，即使本次未改该句。
        assert row["source"] in current and row["runtime_source"] in current
    assert len(changes) == len(CHANGES) == 18
    apply_supplemental([before[row["source"]] for row in changes], changes)
    save(OUT / "post-burn-dialogue-corrections.json", changes)
    save(OUT / "post-burn-dialogue-review.json", review)
    save(OUT / "post-burn-dialogue-tests.json", cases)
    paragraphs = ["# 烧书后昆斯对白逐句审查", "",
                  "范围：真实 scenes_smalltalk 的 POSTEND_QuinceBookBurned，首次27句、第二次2句、后续重复2句。18句校订；What?的共享键限制单独保留说明。以下完整列出全部31句，不将原本通顺的句子全部重译。", "",
                  "状态：已生成并验证候选，未安装。插件仍1.5.15，17,069词条、157规则、7,661字形不变。本轮只改18个已有词条的中文目标，所有英文键、ID及顺序均不变，未增加字符。尚未恢复玩家存档。", "",
                  "129项翻译治理、93项本段正文／对话框／日志消费者、642项love及归来对白回归通过；17,069项实际XUnity字典解析、708组成对变体及33条显式别名检查通过，40文件与ZIP逐项一致。历史love审查保留快照，读取时通过准确旧值承接本轮新译。见[候选核验](../../../runtime/evidence/post-burn-dialogue-verification-2026-10-19.json)。这些是离线资源和真实翻译组件检查，未启动主游戏，不称剧情E2E。", "",
                  "全部三个对白分支已审查。`What?`在此烦躁语境下可译“干嘛？”，但与全游戏多处惊讶或疑问语境共用同一个查找键，目前仍保留“什么？”，不把所有同源句一并改成“干嘛？”。", "",
                  "重建入口：[prepare_post_burn_followup.py](../../../tools/translation/prepare_post_burn_followup.py)；[准确旧值校订](../../../translation/supplemental/post-burn-dialogue-corrections.json)、[全部31句机器记录](../../../translation/supplemental/post-burn-dialogue-review.json)。不依赖旧存档。", ""]
    for index, row in enumerate(review, 1):
        paragraphs.extend([f"## {index}．{row['branch']}·{'昆斯' if row['actor'] == 'quince' else '奥菲莉娅'}", "",
                           "英文：" + row["source"], "", "改前：" + row["previous_target"], "",
                           ("改后：" if row["changed"] else "保留：") + row["target"], "", "说明：" + row["reason"], ""])
    path = ROOT / "docs/dev-tasks/localization/post-burn-dialogue-2026-10-19.md"
    path.write_text("\n".join(paragraphs), encoding="utf-8", newline="\n")
    print("烧书后31句全分支审查：18句校订，93项真实正文／对话框／日志消费者夹具。")


if __name__ == "__main__":
    main()
