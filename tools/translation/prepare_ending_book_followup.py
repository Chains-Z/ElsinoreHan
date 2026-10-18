"""从真实结局元数据生成命运之书标题补译，不改写游戏业务数据。"""

import base64
import hashlib
import json
from prepare_dialogue_log_followup import ROOT, GAME_RESOURCE, read, save
from analyze import read_text_assets


WORDS = {
    "STRUGGLE": "挣扎", "RELIEF": "解脱", "PRESTIGE": "地位", "FAMILY": "家人",
    "INNOCENCE": "纯真", "POWER": "权力", "MORTALITY": "凡躯", "GODHOOD": "神格",
    "LEGACY": "基业", "REALITY": "现实", "JOY": "欢乐", "ETERNITY": "永恒",
    "REVENGE": "复仇", "PEACE": "和平", "SURVIVAL": "生存", "PERMANENCE": "厮守",
    "PASSION": "激情", "PREDICTABILITY": "安稳", "ADVENTURE": "冒险",
    "EVERYONE": "众人", "MYSELF": "自我", "RESPONSIBILITY": "责任",
    "INDULGENCE": "享乐", "INDEPENDENCE": "独立",
}

TITLE_CORRECTIONS = {
    "LEGACY": ("传承", "用户2026-10-18确认：结合与哈姆雷特共同治理丹麦、延续王权的结局语境，改为基业；不补写子嗣"),
    "PRESTIGE": ("声望", "用户2026-10-18要求准确二字标题；流放失去的是贵族与宫廷地位，不仅是名声"),
    "MORTALITY": ("凡人之身", "用户2026-10-18要求所有标题词为二字；用凡躯承接凡人之身与终有一死的存在状态，和神格对应"),
    "PERMANENCE": ("长久", "用户2026-10-18要求将长相厮守压为二字；以厮守表达爱情长久相伴这一语境，不增加永生或子嗣含义"),
    "EVERYONE": ("所有人", "用户2026-10-18要求所有标题词为二字；以众人指代被抛在身后的家人朋友等其他人，不改为杀死所有人"),
    "INDULGENCE": ("纵情", "用户2026-10-18确认统一准确二字标题；享乐更清楚表达饮酒游荡寻欢与放下责任的对照"),
    "MYSELF": ("自己", "用户2026-10-18要求重新考虑二字标题；候选采用自我，表达选择属于自己的人生，避免独活将其缩成仅仅保命"),
}


def main():
    asset = next((sha, text) for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())
                 if name == "endings" and "END_Resignation" in text)
    endings = json.loads(asset[1])["endings"]
    assert set(WORDS) == {row[field] for row in endings for field in ("sacrifice-what", "sacrifice-for")}
    previous = {row["source"]: row["target"] for row in read(ROOT / "translation/sol-full-2026-10-09/translations.json")
                if not row["id"].startswith("ui-ending-")}
    translations, tests, pages = [], [], []
    for source, target in list(WORDS.items()) + [("<i>Sacrifice</i>", "<i>舍弃</i>"), ("<i>for</i>", "<i>换取</i>")]:
        digest = hashlib.sha256(source.encode()).hexdigest()
        origins = [{"asset": "endings", "asset_sha256": asset[0], "record_id": row["id"], "field": field}
                   for row in endings for field in ("sacrifice-what", "sacrifice-for") if row[field] == source]
        if not origins:
            origins = ["真实UI_Book_BackGround2书页印字；EndingBookLabels创建的斜体文本源"]
        item = {"id": "ui-ending-" + digest[:16], "source": source, "target": target,
                "source_sha256": digest, "origins": origins,
                "translation_method": "根据真实结局语境定向补译；保持四行牺牲与换取的对应关系"}
        if source in previous and previous[source] != target:
            item["previous_target"] = previous[source]
        if source in TITLE_CORRECTIONS:
            item["previous_target"], item["correction_reason"] = TITLE_CORRECTIONS[source]
        translations.append(item)
        tests.append({"id": item["id"], "source": source, "target": target})
    for row in endings:
        pages.append({"id": row["id"], "inbook": row["inbook"],
                      "what_source": row["sacrifice-what"], "what_target": WORDS[row["sacrifice-what"]],
                      "for_source": row["sacrifice-for"], "for_target": WORDS[row["sacrifice-for"]]})
    save(ROOT / "translation/supplemental/ending-book-translations.json", translations)
    save(ROOT / "translation/supplemental/ending-book-tests.json", tests)
    save(ROOT / "runtime/build/ending-book/source-audit.json", {"asset_sha256": asset[0], "pages": pages})
    enc = lambda text: base64.b64encode(text.encode()).decode()
    path = ROOT / "runtime/build/ending-book/pages.tsv"
    path.write_text("".join("\t".join([p["id"], str(p["inbook"]), enc(p["what_source"]), enc(p["what_target"]),
                                      enc(p["for_source"]), enc(p["for_target"])]) + "\n" for p in pages), encoding="utf-8")
    print(json.dumps({"pages": len(pages), "book_pages": sum(p["inbook"] for p in pages), "translations": len(translations)}))


if __name__ == "__main__":
    main()
