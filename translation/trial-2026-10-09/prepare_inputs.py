"""从本机真实资源复建小样；不联网、不读密钥、不调用模型。"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "tools" / "translation"))
import analyze
import prepare_pilot

OUT = Path(__file__).resolve().parent


def write_json(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    assets = list(analyze.read_text_assets((analyze.GAME / "resources.assets").read_bytes()))

    def asset(name):
        return max(((d, b) for n, d, b in assets if n == name), key=lambda x: len(x[1]))

    names_digest, names_body = asset("name_mapping")
    names = analyze.read_json(names_body)
    digest, body = asset("scenes")
    lines = body.splitlines()
    dialogues = {r["source_line"]: r for r in prepare_pilot.read_dialogues(body, digest, names)}
    entries = []

    def dialogue(line, batch, register, context):
        row = dict(dialogues[line])
        row.update(batch=batch, register=register, context=context,
                   origin=f"resources.assets:scenes:{digest}:line:{line}",
                   source_raw_line=lines[line - 1])
        entries.append(row)

    # 明确选择鬼魂初遇后分支中的第一次暂停世界路径，跳过互斥的 else。
    main_lines = [line for line in dialogues if 374 <= line <= 412 and line not in (387, 388)]
    assert len(main_lines) == 20
    for line in main_lines:
        dialogue(line, "01_hamlet_ghost_followup", "自然对白；Quince 略有戏剧感，Hamlet 慌乱",
                 "这20条在已注明的单一路径内按真实脚本顺序排列；不要混入其他循环的台词。")

    challenges = [
        (206, "古雅戏剧开场", "Quince 的原文使用 How now / Whither；其后的 Ophelia 回答 Ah. Quince.（207行）。这不是 Hamlet 批次的延续。"),
        (209, "日常关切", "与206、207同行场；Quince 接着说 You sound terribly glum.；Ophelia 在210行说她很久未想到 Elsinore、如今想回去。勿据前句的古雅把本句文言化。"),
        (16566, "戏中戏古雅反问和富文本强调", "16564行 Katherine 说 W-what, in the midst of the street?；16566、16567为相邻对话，使用舞台角色名 Petruchio / Katherine。"),
        (16567, "戏中戏否定与害羞对象", "紧接16566行 What, art thou <i>ashamed</i> of me?；不能把 ashamed to kiss 改成羞于对方本人。"),
        (21207, "祈祷庄重语体", "FLAVOR_BernardoPraying；21206行动提示 am_cross，21207与21208连续，21210继续 And blessed is the fruit of thy womb...。"),
        (21208, "祈祷古雅语体", "紧接21207行 Hail Mary, full of grace, the Lord is with thee.；引用祈祷文，非日常搭话。"),
        (25854, "讥讽、侮辱和古雅词混用", "25851行 Ophelia 说 We don't <i>have</i> to be at odds.；Brit 此句演出提示 [disgust] {Spare_Me}；25856是Ophelia内心话。"),
        (25856, "内心话、否定与不确定性", "紧接 Brit 在25854行的拒绝。括号表示原文内心话；must 不得擅加到 wonder/maybe；保留两个 <b> 区间。"),
        (16694, "格言引用", "16693行 Ophelia 对 Bernardo 说 Bernardo—Katherine—whomever you desire to be...；本句明确引用父亲的格言。不要根据原著替角色猜性别。"),
        (471, "否定、确信与富文本", "属于 HamletStarter 的 occurrenceCount(...)=2 分支，470行为 Why am I still alive? I thought...；本条是 No. I <i>know</i> I died.；与主批次互斥，单独评阅。"),
    ]
    for line, register, context in challenges:
        dialogue(line, "02_register_challenges", register, context)

    def field_row(name, obj_path, text, batch, context, speaker_id=None, register="清楚准确的界面/资料语体"):
        adigest, abody = asset(name)
        literal = json.dumps(text, ensure_ascii=False)
        matches = [i for i, line in enumerate(abody.splitlines(), 1) if literal in line]
        if not matches:
            raise ValueError(f"无法定位原始 JSON 字段: {name}/{obj_path}")
        # 根据字段键及对象 ID 消歧，避免把同文 short 或其他对象当成来源。
        source_lines = abody.splitlines()
        exact_matches = matches
        if not obj_path.startswith("categories["):
            key = obj_path.rsplit(".", 1)[1]
            exact_matches = [n for n in matches if f'"{key}":' in source_lines[n - 1]]
            selected_object = re.search(r'\[(id|constant)=([^\]]+)\]', obj_path)
            if selected_object and len(exact_matches) > 1:
                object_key, object_value = selected_object.groups()
                object_literal = f'"{object_key}": {json.dumps(object_value)}'
                object_line = next(n for n, raw in enumerate(source_lines, 1) if object_literal in raw)
                next_object_line = next((n for n in range(object_line + 1, len(source_lines) + 1)
                                         if f'"{object_key}":' in source_lines[n - 1]), len(source_lines) + 1)
                exact_matches = [n for n in exact_matches if object_line < n < next_object_line]
            if len(exact_matches) != 1:
                raise ValueError(f"字段来源行无法消歧: {obj_path} {exact_matches}")
        exact_line = exact_matches[0]
        row = dict(id=f"{name}:{adigest[:12]}:{obj_path}", scene=obj_path,
                   speaker_id=speaker_id, name=names.get(speaker_id) if speaker_id else None,
                   message=text, source_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                   source_asset_sha256=adigest, source_line=exact_line,
                   source_raw_line=source_lines[exact_line - 1],
                   source_line_candidates=matches, source_json_path=obj_path,
                   origin=f"resources.assets:{name}:{adigest}:{obj_path}",
                   acting_cues="", batch=batch, register=register, context=context)
        entries.append(row)

    chars_digest, chars_body = asset("characters")
    chars = analyze.read_json(chars_body)["characters"]["actors"]
    for speaker in ("marcellus", "rosencrantz"):
        actor = next(x for x in chars if x["id"] == speaker)
        context = "characters.actors 的真实 presentline，角色交谈入口，不是前面场景的延续。"
        if speaker == "rosencrantz":
            context += "name_mapping 明确为 Lady Rosencrantz；bios 的角色条目也称她 she，不得按原著改作男性。"
        field_row("characters", f"characters.actors[id={speaker}].presentline", actor["presentline"],
                  "02_register_challenges", context, speaker,
                  "粗犷口语与礼貌称谓" if speaker == "marcellus" else "略正式、自我调侃")

    inf_digest, inf_body = asset("information")
    inf = analyze.read_json(inf_body)
    for category in ("All", "Otherworldly Occurrences"):
        field_row("information", f"categories[{inf['categories'].index(category)}]", category,
                  "03_ui_and_information", "资料界面的分类标题。")
    for ident, field in (("Assassin_PlayHearsay", "name"), ("Assassin_PlayHearsay", "long"),
                         ("Dad_PlayHearsay", "long"), ("InconvenientAffections", "long")):
        item = next(x for x in inf["information"] if x["id"] == ident)
        context = f"information[id={ident}]，type={item.get('type')}；这是角色取得的资料表述，不得升格为全知事实。"
        if ident == "Dad_PlayHearsay":
            context += "my father 的第一人称参照 Ophelia；保留 will 和 not even。"
        field_row("information", f"information[id={ident}].{field}", item[field],
                  "03_ui_and_information", context)
    kd, kb = asset("knowledge")
    mapping = analyze.read_json(kb)["mapping"]
    for constant in ("ghostrumors", "fortinbras_offer"):
        item = next(x for x in mapping if x["constant"] == constant)
        field_row("knowledge", f"mapping[constant={constant}].text", item["text"],
                  "03_ui_and_information", "知识/信念条目标签；只翻译可见 text，代码常量不翻译。rumors 是传闻，cross Denmark 不擅改成 invade。")

    batches = []
    for batch in dict.fromkeys(x["batch"] for x in entries):
        members = [x for x in entries if x["batch"] == batch]
        filename = f"{batch}.json"
        write_json(f"inputs/{filename}", [{k: r[k] for k in ("name", "message") if r[k] is not None} for r in members])
        for index, row in enumerate(members):
            row.update(file=filename, index=index)
        batches.append(dict(id=batch, file=filename, count=len(members), continuous=batch.startswith("01")))

    assert len(entries) == 40 and len({r['id'] for r in entries}) == 40
    contexts = {
        "01_hamlet_ghost_followup": {
            "continuous": True,
            "selected_outer_branch_line": 355,
            "selected_outer_branch": "((occurrenceCount(SC_GHUNT_GhostAppears) = 1) && previously occurred(SC_GHUNT_GhostAppears))",
            "selected_inner_branch_line": 383,
            "selected_inner_branch": "occurrenceCount(SC_OTH_OthelloConsummate) = 0",
            "excluded_mutually_exclusive_lines": [387, 388],
            "note": "只选择主 elif 链的鬼魂初遇后分支；312、334等更早elif分支此路径不成立。脚本以前的独立if块不收入本段，不能据本段推定它们的真假。",
            "background": "Quince 与 Ophelia 在她卧室交谈，Hamlet 在场。Ophelia 说她以为 King Hamlet 已死，Quince 表示确已死但死亡不是线性的，二人和自己均有未竟之事；Ophelia/Quince 对白随后明确世界在重复。Hamlet 的动作暂停，后被恢复。随后 Hamlet 说自己见到了父亲的亡魂，地点是城墙，时间是午夜。背景只作理解参照，不提前加进任何译句。",
            "evidence_lines": [360, 368, 369, 372, 374, 376, 377, 380, 383, 384, 385, 393, 398, 400, 402, 405, 412],
            "preceding_context": [{"speaker": dialogues[n]['name'], "source": dialogues[n]['message'], "line": n} for n in (368, 369, 372, 373)],
        },
        "02_register_challenges": {"continuous": False, "note": "各项自带源自原文的只读context。仅206/209、16566/16567、21207/21208、25854/25856各对在各自场景内关联；不同场景之间不可串成连续对话。"},
        "03_ui_and_information": {"continuous": False, "note": "独立界面字段、传闻资料与信念标签；只读context指明事实强度和第一人称参照。"},
    }
    # 再核对女性称谓的真实 bios 证据，不借原著设定补全。
    bd, bb = asset("bios")
    bios = analyze.read_json(bb)["list"]
    female_evidence = []
    for ident in ("rosencrantz", "guildenstern"):
        item = next(x for x in bios if x["id"] == ident)
        female_evidence.append(dict(id=ident, name_mapping=names[ident], source_asset_sha256=bd,
                                   source_json_path=f"list[id={ident}]", evidence=item))
    write_json("context.json", {"source_asset_sha256": digest, "batches": contexts,
                               "character_evidence": female_evidence})
    terms = [("Ophelia", "奥菲莉娅"), ("Hamlet", "哈姆雷特"), ("King Hamlet", "哈姆雷特国王"),
             ("Quince", "奎因斯"), ("Elsinore", "埃尔西诺"), ("Fortinbras", "福丁布拉斯"),
             ("Claudius", "克劳狄斯"), ("Bernardo", "贝尔纳多"), ("Katherine", "凯瑟琳"),
             ("Petruchio", "彼特鲁乔"), ("Brit", "布莉特"), ("Marcellus", "马塞勒斯"),
             ("Lady Rosencrantz", "罗森克兰兹女士"), ("Lady Guildenstern", "吉尔登斯吞女士")]
    write_json("glossary.json", {"status": "proposal", "note": "供本轮候选统一使用的暂定译法，尚未经用户确认，不是正式锁定词表。Lady 的中文称谓后续结合游戏关系调整，不因原著假设婚姻或男性身份。",
                                "entries": [{"source": s, "target": t, "status": "proposal"} for s, t in terms]})
    write_json("manifest.json", {"format": "VNText", "model_calls": 0, "count": len(entries),
                                "input_root": "inputs", "batches": batches,
                                "name_mapping_asset_sha256": names_digest,
                                "limitations": ["静态最大候选资产，未经动态确认为游戏实际加载版本", "上下文为原文核对所得，不证明剧情全覆盖", "仅第一批连续；挑战/资料批次按条目独立理解", "VNText输出会丢失元数据，须按manifest核对数量/顺序/原文后恢复ID"],
                                "entries": entries})
    print(json.dumps({"count": len(entries), "batches": batches,
                      "source_characters": sum(len(r['message']) for r in entries),
                      "model_calls": 0}, ensure_ascii=True))


if __name__ == "__main__":
    main()
