"""离线复建 300 条真实游戏扩展样本，不读凭证或调用模型。"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OLD = ROOT / "translation/trial-2026-10-09"
sys.path[:0] = [str(ROOT / "analysis"), str(ROOT / "tools/translation")]
import analyze
import prepare_pilot

# 范围内均无改变对白路径的条件；片段前的条件作为只读来源保留。
RANGES = [
    (810, 831, "guards_hamlet", "马塞勒斯劝哈姆雷特参加朝会；粗犷口语与慌乱对白", "Marcellus urges Hamlet to attend court; colloquial speech and distress"),
    (837, 853, "guards_hamlet_followup", "哈姆雷特与马塞勒斯谈及昨夜所见和叔父", "Hamlet and Marcellus discuss what they saw last night and Hamlet's uncle"),
    (11260, 11297, "garden_horatio", "花园散步，王后询问霍拉旭的经历；称谓与家人关系", "Gertrude asks Horatio about his past during a garden walk; forms of address and family relations"),
    (11307, 11352, "garden_gertrude", "另一次花园散步，王后讲述童年和姐姐；国王哈姆雷特与王子须分清", "A separate garden walk: Gertrude recalls her childhood and elder sister; distinguish King Hamlet from the prince"),
    (16376, 16402, "errand_fountain", "两位女士取喷泉里的苔藓；幽默反讽与强调", "The two ladies collect moss from a fountain; humor, irony and emphasis"),
    (16408, 16420, "errand_book", "另一个场景，两位女士在找书；包含德文书名", "A separate scene: the two ladies search for a book; a German book title appears"),
    (16424, 16430, "errand_portrait", "同一场景中的肖像话题片段；与找书片段分批，传闻不可升格事实", "A portrait discussion from the same scene, batched separately; preserve hearsay as hearsay"),
    (16434, 16435, "errand_exit", "同场景收尾；此前两条省略号不列为付费样本", "The conclusion of the same scene; preceding ellipsis-only lines are not paid translation samples"),
    (16443, 16459, "errand_gathering", "另一次差事；十二进制数量和饥饿抱怨", "A separate errand; a quantity in dozens and a complaint about hunger"),
    (18444, 18460, "bernardo_leaving", "贝尔纳多宣布离开，未给具体理由；未来与不确定性", "Bernardo announces his departure without giving a specific reason; future and uncertainty"),
    (10104, 10118, "elise_grief", "母亲墓前回忆；选择不知纪念日的 else 路径，不混入已知分支", "Memories at Mother's grave; select the else branch where Ophelia does not know the anniversary"),
    (6376, 6391, "irma_gertrude", "王后和厨娘谈怀疑与饭菜；片段从条件汇合之后开始", "Gertrude and Irma discuss suspicion and food; the excerpt starts after branch convergence"),
    (24730, 24735, "crew_grace_family", "船员谈女船长，乡音与非字面比喻；后续条件内心话不列入", "Crewmen discuss their captain; dialect and figurative language; subsequent conditional thoughts are excluded"),
    (24749, 24758, "crew_grace_divorce", "另次船员交谈；婚姻时间、离婚和夸张粗话", "A separate crew conversation; marriage dates, divorce and exaggerated coarse language"),
    (24772, 24787, "crew_grace_queen", "第三次船员交谈和船长发现偷听；保留否定与条件", "A third crew conversation and the captain discovering eavesdropping; preserve negation and conditions"),
    (745, 768, "polonius_lecture", "父亲责问女儿；选择 loop<=2 且 loop!=2 的首次路径，排除返场和第二轮", "A father's rebuke; select the first-loop branch (loop<=2 and loop!=2), excluding return and second-loop alternatives"),
]

CHALLENGES = [
    ([1480,1481,1484,1486,1489,1491,1515,1517,1524,1525], "名句改写、情绪否认与内心话", "Adapted famous speech, emotional denial and internal thought"),
    ([2661,2662,2669,2670,2671,2672,2673,2676,2687,2688,2693,2695], "忏悔、亲属关系、祈祷与假设", "Confession, family relations, prayer and hypothetical statements"),
    ([19179,19181,19183,19185,19187,19191,19205,19208], "歌谣诗句、古雅缩写和口语比喻", "Song verses, archaic contractions and colloquial imagery"),
    ([21210,21221,21223,21229,21230,21233,21240,21244,21249,21264], "祈祷、宗教讨论、讥讽和否定", "Prayer, discussion of religion, sarcasm and negation"),
    ([6417,6418,6419,6420,6423,6424,6425,6426], "丧亲慰藉、委婉死亡与非字面表达", "Consolation in bereavement, euphemistic death and figurative expressions"),
    ([21156,21160,21162,21165,21171,21172,21173,21177,21191,21193,21198,21199], "循环、生死、时态自我修正和条件", "Time loops, life and death, self-correction of tense and conditions"),
]

# 仅传入与选定路径兼容的前文，避免按行号截取而带入互斥分支。
PRECEDING_LINES = {
    "garden_horatio": [11245,11247,11249,11251,11254],
    "garden_gertrude": [11302,11305],
    "errand_portrait": [16419,16420],
    "errand_exit": [16427,16429,16430],
    "elise_grief": [10096,10097],
    "irma_gertrude": [6367,6369],
}


def write_json(path, value):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    assets = list(analyze.read_text_assets((analyze.GAME / "resources.assets").read_bytes()))

    def asset(name):
        return max(((d, b) for n, d, b in assets if n == name), key=lambda x: len(x[1]))

    nd, nb = asset("name_mapping")
    names = analyze.read_json(nb)
    digest, body = asset("scenes")
    raw_lines = body.splitlines()
    dialogues = {r["source_line"]: r for r in prepare_pilot.read_dialogues(body, digest, names)}
    old_manifest = json.loads((OLD / "manifest.json").read_text(encoding="utf-8"))
    old_norm = {analyze.normalize(r["message"]) for r in old_manifest["entries"]}
    seen = set(old_norm)
    entries, contexts = [], {}

    def add(row, batch, category, register, context, english, english_register=None):
        norm = analyze.normalize(row["message"])
        if norm in seen:
            raise ValueError(f"重复原文: {row['id']}")
        seen.add(norm)
        row.update(batch=batch, category=category, register=register, context=context,
                   qwen_mt_context=english, qwen_mt_register=english_register or english)
        entries.append(row)

    def dialogue(line):
        row = dict(dialogues[line])
        row.update(origin=f"resources.assets:scenes:{digest}:line:{line}",
                   source_raw_line=raw_lines[line - 1])
        return row

    for ordinal, (start, end, slug, note, english) in enumerate(RANGES, 1):
        batch = f"d{ordinal:02d}_{slug}"
        # 不借原著补人物身份；只引用本游戏名称映射与原文。
        prior = [dialogues[n] for n in PRECEDING_LINES.get(slug, [])]
        preceding = [{"speaker": r["name"], "source": r["message"], "line": r["source_line"]} for r in prior]
        contexts[batch] = {"continuous": True, "background": note,
                           "qwen_mt_background": english, "source_line_range": [start, end],
                           "preceding_context": preceding,
                           "note": "只表示这一真实脚本片段内的连续路径；不同 batch 不串成一次对话。"}
        for line in sorted(dialogues):
            if start <= line <= end:
                add(dialogue(line), batch, "dialogue", note, note, english)
    assert len(entries) == 180

    for ordinal, (selected, note, english) in enumerate(CHALLENGES, 1):
        batch = f"c{ordinal:02d}_register_challenges"
        contexts[batch] = {"continuous": False, "note": "同组围绕一个话题选句，各条仍独立；原始邻近行供只读语境，不能视为完整连续对话。"}
        for line in selected:
            # 原始控制语句留在邻近证据里，不把条件分支拼成实际发生的事件。
            excerpt = "\n".join(f"{n}: {raw_lines[n-1]}" for n in range(max(1,line-3), min(len(raw_lines),line+3)+1))
            preceding = []
            for n in range(line-1, max(0,line-9), -1):
                # 碰到分支界线就停止，不把上一条互斥路径传给模型。
                if re.match(r"\s*(?:if\b|elif\b|else\b|endif\b|call\b|\{[A-Za-z_])", raw_lines[n-1]):
                    break
                if n in dialogues:
                    preceding = [{"speaker": dialogues[n]["name"], "source": dialogues[n]["message"], "line": n}]
                    break
            prior = json.dumps(preceding, ensure_ascii=False)
            context = f"真实场景 {dialogues[line]['scene']}，源行 {line}；只读前一句：{prior}。各条独立，不跨分支推定。"
            qwen_context = f"Scene {dialogues[line]['scene']}, source line {line}; read-only preceding line: {prior}. Entries are independent; do not infer events across branches."
            row = dialogue(line)
            row.update(source_neighborhood=excerpt, preceding_context=preceding)
            add(row, batch, "challenge", note, context, qwen_context, english)
    assert len(entries) == 240

    def field_row(asset_name, path, field, text, context, english):
        ad, ab = asset(asset_name)
        literal = json.dumps(text, ensure_ascii=False)
        matches = [n for n, raw in enumerate(ab.splitlines(), 1)
                   if literal in raw and (field is None or f'"{field}":' in raw)]
        source_lines = ab.splitlines()
        if path.startswith("categories["):
            # 顶层分类在对象列表前；同名分类也会出现在每个资料对象中。
            first_object = next(n for n, raw in enumerate(source_lines, 1) if '"information":' in raw)
            matches = [n for n in matches if n < first_object]
        elif asset_name in ("information", "knowledge"):
            identity = re.search(r"\[(id|constant)=([^\]]+)\]", path)
            key, value = identity.groups()
            marker = f'"{key}": {json.dumps(value)}'
            start = next(n for n, raw in enumerate(source_lines, 1) if marker in raw)
            stop = next((n for n in range(start + 1, len(source_lines) + 1)
                         if f'"{key}":' in source_lines[n-1]), len(source_lines)+1)
            matches = [n for n in matches if start < n < stop]
        if len(matches) != 1:
            raise ValueError(f"字段来源须唯一: {asset_name}/{path}: {matches}")
        line = matches[0]
        return {"id": f"{asset_name}:{ad[:12]}:{path}", "scene": path,
                "speaker_id": None, "name": None, "message": text,
                "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "source_asset_sha256": ad, "source_line": line,
                "source_raw_line": ab.splitlines()[line-1], "source_json_path": path,
                "origin": f"resources.assets:{asset_name}:{ad}:{path}", "acting_cues": ""}, context, english

    ui = []
    _, ib = asset("information")
    information = analyze.read_json(ib)
    for index, text in enumerate(information["categories"]):
        if analyze.normalize(text) not in seen:
            ui.append(field_row("information", f"categories[{index}]", None, text,
                                "资料界面分类标题。", "Information menu category title."))

    def choose_information(field, count):
        selected = 0
        # 轮流覆盖不同分类，避免只取原文件开头的宫廷资料。
        groups = {}
        for item in information["information"]:
            category = next((x for x in item.get("categories", []) if x != "All"), "All")
            groups.setdefault(category, []).append(item)
        for depth in range(max(map(len, groups.values()))):
            for group in groups.values():
                if depth >= len(group):
                    continue
                item = group[depth]
                text = item.get(field, "")
                if not text or analyze.normalize(text) in seen or any(analyze.normalize(row[0]["message"]) == analyze.normalize(text) for row in ui):
                    continue
                context = f"奥菲莉娅资料表，条目 {item['id']}，类型 {item.get('type')}；保留传闻/可能性和第一人称，不翻译程序条件。"
                english = f"Ophelia's information entry {item['id']}, type {item.get('type')}; preserve hearsay, uncertainty and first-person reference; program conditions are not translation targets."
                ui.append(field_row("information", f"information[id={item['id']}].{field}", field, text, context, english))
                selected += 1
                if selected == count:
                    return
        raise ValueError("资料候选不足")

    choose_information("name", 15)
    choose_information("long", 20)
    _, kb = asset("knowledge")
    mapping = analyze.read_json(kb)["mapping"]
    selected = 0
    for item in mapping:
        text = item.get("text", "")
        if not text or analyze.normalize(text) in seen or any(analyze.normalize(row[0]["message"]) == analyze.normalize(text) for row in ui):
            continue
        ui.append(field_row("knowledge", f"mapping[constant={item['constant']}].text", "text", text,
                            "知识/信念的可见标签；只翻译 text，不翻译 constant。", "Visible knowledge or belief label; translate text, not the program constant."))
        selected += 1
        if selected == 10:
            break
    _, bb = asset("bios")
    bios = analyze.read_json(bb)["list"]
    selected = 0
    for item in bios:
        initial = next((r for r in item.get("lines", []) if r["id"] == "initial"), None)
        if not initial or analyze.normalize(initial["text"]) in seen:
            continue
        ui.append(field_row("bios", f"list[id={item['id']}].lines[id=initial].text", "text", initial["text"],
                            f"奥菲莉娅视角的角色资料 {item['id']}；保留原有不确定性、换行和身份表述。", f"Character biography {item['id']} from Ophelia's perspective; preserve uncertainty, line breaks and identity as written."))
        selected += 1
        if selected == 8:
            break
    assert len(ui) == 60
    for index, (row, context, english) in enumerate(ui):
        batch = f"u{index // 15 + 1:02d}_ui_information"
        contexts[batch] = {"continuous": False, "note": "各项独立资料字段；不能串接为同一段故事。"}
        add(row, batch, "ui", "清楚准确的界面/资料语体", context, english, "Clear and precise UI or information prose")

    batches = []
    for batch in dict.fromkeys(row["batch"] for row in entries):
        members = [row for row in entries if row["batch"] == batch]
        filename = batch + ".json"
        for index, row in enumerate(members):
            row.update(file=filename, index=index)
        write_json("inputs/" + filename, [{k: row[k] for k in ("name", "message") if row[k] is not None} for row in members])
        batches.append({"id": batch, "file": filename, "count": len(members), "continuous": contexts[batch]["continuous"]})
    assert len(entries) == 300 and len({r["id"] for r in entries}) == 300
    assert len({analyze.normalize(r["message"]) for r in entries}) == 300
    assert not old_norm.intersection(analyze.normalize(r["message"]) for r in entries)
    for row in entries:
        assert row["source_text_sha256"] == hashlib.sha256(row["message"].encode()).hexdigest()

    glossary = json.loads((OLD / "glossary.json").read_text(encoding="utf-8"))
    write_json("glossary.json", glossary)
    old_context = json.loads((OLD / "context.json").read_text(encoding="utf-8"))
    write_json("context.json", {"source_asset_sha256": digest, "batches": contexts,
                                "character_evidence": old_context["character_evidence"]})
    for batch in batches:
        members = [row for row in entries if row["batch"] == batch["id"]]
        facts = contexts[batch["id"]]
        if batch["continuous"]:
            prior = json.dumps(facts["preceding_context"], ensure_ascii=False)
            background = facts["background"] + "\n只读前文：" + prior
            domains = facts["qwen_mt_background"] + "\nRead-only preceding lines: " + prior
        else:
            background = "条目彼此独立，只读语境不额外翻译：\n" + "\n".join(f"{r['index']+1}. {r['context']}；语体：{r['register']}" for r in members)
            domains = "Independent entries. Context is read-only, not a translation target.\n" + "\n".join(f"{r['index']+1}. {r['qwen_mt_context']}; register: {r['qwen_mt_register']}" for r in members)
        source = "\n".join((r.get("name") or "") + " " + r["message"] for r in members)
        terms = [{"src": t["source"], "dst": t["target"], "info": "本轮暂定译名，跨模型统一，未经过用户确认"}
                 for t in glossary["entries"] if t["source"].lower() in source.lower()]
        write_json("rules/" + batch["id"] + ".json", {
            "prompt_dictionary_switch": True, "prompt_dictionary_data": terms,
            "world_building_switch": True, "world_building_content": background,
            "qwen_mt_domains": domains,
            "characterization_switch": False, "translation_memory_switch": False,
            "translation_example_switch": False})
    for filename in ("system-prompt.txt", "writing-style.txt"):
        shutil.copyfile(OLD / filename, OUT / filename)
    metrics = {"count": len(entries), "categories": dict(Counter(r["category"] for r in entries)),
               "source_characters": sum(len(r["message"]) for r in entries),
               "source_words": sum(len(analyze.WORD.findall(r["message"])) for r in entries),
               "batches": len(batches), "old_sample_overlap": 0, "duplicate_normalized_texts": 0,
               "model_calls": 0}
    write_json("manifest.json", {"format": "VNText", **metrics, "input_root": "inputs", "batches": batches,
                                "name_mapping_asset_sha256": nd,
                                "limitations": ["静态最大资源候选，未经动态确认实际加载版本", "连续只限单个片段，不代表不同片段接续发生", "定向选样，不是随机样本，不能估计全量错误率", "Qwen 英文 domains 与通用模型中文规则传达同一背景，协议不同不等于提示完全相同", "VNText 丢失元数据，须按 file/index 恢复真实来源 ID"],
                                "entries": entries})
    write_json("source-verification.json", {**metrics, "source_hashes": {name: asset(name)[0] for name in ("scenes", "information", "knowledge", "bios", "name_mapping")},
                                             "source_reconstructed_from_game": True, "all_entry_text_hashes_passed": True})
    print(json.dumps(metrics, ensure_ascii=True))


if __name__ == "__main__":
    main()
