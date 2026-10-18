"""从单一规范译文与准确格式合同生成消费者预期，不读取消费者实际输出作答案。"""

import re

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, digest, read, save, short_name
from source_variant_generation import wrap


DIRECTORY = ROOT / "translation/supplemental"


def main():
    canonical = {row["id"]: row for row in read(DIRECTORY / "canonical-variant-translations.json")}
    manifest = read(DIRECTORY / "generated-variant-bindings.json")
    expected = {row["source"]: {"target": wrap(canonical[row["canonical_id"]]["target"], row["prefix"], row["suffix"]),
                               "origins": canonical[row["canonical_id"]]["origins"]}
                for row in manifest["bindings"]}
    generated_sources = set(expected)
    for filename in ("playmaster-title-corrections.json", "victory-dinner-corrections.json", "playmaster-tone-corrections.json"):
        for row in read(DIRECTORY / filename):
            if row["source"] in generated_sources:
                # 称号先覆盖历史阶段，再由规范译文统一同句措辞；不能倒写旧快照。
                assert filename == "playmaster-title-corrections.json"
                assert "戏剧大师" in expected[row["source"]]["target"]
                continue
            expected[row["source"]] = row
    # 保留裸源共享应答；本轮只调整前句，不泛化覆盖Of course。
    expected["Of course."] = {"target": "当然。", "origins": ["VictoryDinner及其他13处真实应答"]}
    rows = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row for row in rows}
    title_rows = [row for row in rows if re.search(r"\bplaymaster\b", row["source"], re.I)]
    contextual = {row["source"]: row["target"] for row in read(DIRECTORY / "playmaster-tone-corrections.json")
                  if row["strategy"] == "contextual_performer"}
    assert len(contextual) == 3 and len(title_rows) == 33
    assert all(row["target"] == contextual[row["source"]] if row["source"] in contextual
               else "戏剧大师" in row["target"] for row in title_rows)
    assert not any("戏班班主" in row["target"] for row in rows)
    cases = [{"id": "generated-leaf-" + digest(source)[:16], "source": source, "target": row["target"],
              "source_sha256": digest(source), "origins": row["origins"]} for source, row in expected.items()]
    dialogue, _ = extract_rows(rows)
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    seen = set()
    for owner in dialogue:
        source, actor = owner["runtime_source"], owner["actor"]
        if source not in expected or (actor, source) in seen:
            continue
        seen.add((actor, source))
        name = short_name(actor, mapping)
        translated_name = SPECIAL_NAMES.get(name) or targets[name]["target"]
        target = expected[source]["target"]
        for kind, text, value in (
            ("dialogue", "<line-height=90%>" + source, "<line-height=90%>" + target),
            ("log", "<b>" + name + ":</b> <indent=16%>" + source,
             "<b>" + translated_name + ":</b> <indent=16%>" + target)):
            cases.append({"id": "generated-" + kind + "-" + actor + "-" + digest(source)[:16],
                          "source": text, "target": value, "source_sha256": digest(text), "origins": owner["origins"]})
    assert len({row["id"] for row in cases}) == len(cases)
    save(DIRECTORY / "generated-variant-tests.json", cases)
    print({"canonical": len(canonical), "bindings": len(manifest["bindings"]), "leaf_cases": len(expected),
           "runtime_actor_sources": len(seen), "consumer_cases": len(cases)})


if __name__ == "__main__":
    main()
