"""核对全游戏威登堡用词，并生成命运步调与惊惧发声的真实消费者。"""

import re

from audit_dialect_dialogue import extract_rows
from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, digest, read, save, short_name


DIRECTORY = ROOT / "translation/supplemental"


def in_scope(source):
    return bool(re.search(r"wittenb[eu]rg", source, re.I) or "plodding pace of fate" in source
                or source.startswith(("Guh--", "Guh—")))


def main():
    changes = read(DIRECTORY / "place-and-dialogue-corrections.json")
    apply_supplemental([{"id": row["original_id"], "source": row["source"],
                         "target": row["previous_target"]} for row in changes], changes)
    rows = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    # 预期来自审定校订层；既有七条正确地名仍接受全范围断言。
    targets = {row["source"]: dict(row) for row in rows}
    for row in changes:
        targets[row["source"]]["target"] = row["target"]
    selected = {source: row for source, row in targets.items() if in_scope(source)}
    places = [row for row in selected.values() if re.search(r"wittenb[eu]rg", row["source"], re.I)]
    assert len(places) == 39
    assert all("威登堡" in row["target"] and not re.search("维滕贝格|威滕贝格", row["target"]) for row in places)
    assert not any(re.search("维滕贝格|威滕贝格", row["target"]) for row in targets.values())
    assert len(selected) == 45
    dialogue, _ = extract_rows(rows)
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    cases = [{"id": "place-dialogue-leaf-" + row["id"], "source": source,
              "target": row["target"], "source_sha256": digest(source)}
             for source, row in selected.items()]
    seen = set()
    for owner in dialogue:
        source = owner["runtime_source"]
        key = (owner["actor"], source)
        if source not in selected or key in seen:
            continue
        seen.add(key)
        name = short_name(owner["actor"], mapping)
        translated_name = SPECIAL_NAMES.get(name) or targets[name]["target"]
        target = selected[source]["target"]
        for kind, text, expected in (
            ("dialogue", "<line-height=90%>" + source, "<line-height=90%>" + target),
            ("log", "<b>" + name + ":</b> <indent=16%>" + source,
             "<b>" + translated_name + ":</b> <indent=16%>" + target),
        ):
            cases.append({"id": "place-dialogue-" + kind + "-" + owner["actor"] + "-" + digest(source)[:16],
                          "source": text, "target": expected, "source_sha256": digest(text),
                          "origins": owner["origins"]})
    assert len({row["id"] for row in cases}) == len(cases)
    save(DIRECTORY / "place-and-dialogue-tests.json", cases)
    print(f"39条地名全覆盖、45条范围原子、{len(cases)}项消费者已生成")


if __name__ == "__main__":
    main()
