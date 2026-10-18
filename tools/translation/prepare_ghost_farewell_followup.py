"""从真实谢幕幽灵发言生成重复句式及收束对白的消费者用例。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import (
    GAME_RESOURCE, ROOT, SPECIAL_NAMES, digest, read, read_text_assets, save, short_name,
)


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {item["source"]: item["target"] for item in translations}
    rows, _ = extract_rows(translations)
    selected = [next(row for row in rows if row["id"] == identifier)
                for identifier in ("a00334-487149ff01bb", "a00335-36a20b5fb547")]
    shared = [row for row in rows if row["source"] == "That is all."
              or row["runtime_source"] == "<i>That is all.</i>"]
    assert len(shared) == 1 and shared[0]["actor"] == "ghost"
    assert sum(len(row["origins"]) for row in shared) == 1
    # 其它六处只是较长对白中的子串，不属于本次精确词条覆盖范围。
    substring_hits = sum(text.count("That is all.") for _, _, text in read_text_assets(GAME_RESOURCE.read_bytes()))
    assert substring_hits == 7
    expected = ["不要像我那样逃避世界。带着力量向黑暗中前行。带着目标前行。", "我要说的就是这些。"]
    by_actor_source = {(row["actor"], row["source"]): row for row in rows}
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}
    cases = []

    def speaker(row):
        name = short_name(row["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + row["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + row["target"])

    def add(kind, source, target, origins):
        cases.append({"id": "ghost-farewell-" + kind, "source": source, "target": target,
                      "source_sha256": digest(source), "origins": origins})

    for index, row in enumerate(selected):
        assert row["actor"] == "ghost" and row["runtime_source"] == "<i>" + row["source"] + "</i>"
        assert targets[row["source"]] == expected[index]
        assert row["target"] == "<i>" + expected[index] + "</i>"
        assert row["origins"] == [{"asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
                                   "scene": "END_CurtainCall_Resignation", "line": (17211, 17213)[index]}]
        for kind, source, target in (
            ("leaf", row["source"], expected[index]),
            ("italic", row["runtime_source"], row["target"]),
            ("dialogue", "<line-height=90%>" + row["runtime_source"], "<line-height=90%>" + row["target"]),
            ("speaker", *speaker(row)),
        ):
            add(str(index) + "-" + kind, source, target, row["origins"])

    # 同一幽灵发言在日志中连续换行，保留每句真实整体斜体封套。
    pair_source, pair_target = speaker(selected[0])
    pair_source += "\n" + selected[1]["runtime_source"]
    pair_target += "\n" + selected[1]["target"]
    origins = selected[0]["origins"] + selected[1]["origins"]
    add("same-speaker", pair_source, pair_target, origins)
    previous = by_actor_source[("ghost", selected[0]["context"][1]["source"])]
    following = by_actor_source[("ophelia", "Thank you, everyone.")]
    before_source, before_target = speaker(previous)
    assert selected[1]["context"][3] == {"actor": "ophelia", "source": "..."}
    name = short_name(following["actor"], mapping)
    after_source = "<b>" + name + ":</b> <indent=16%>...\n" + following["runtime_source"]
    after_target = "<b>" + targets[name] + ":</b> <indent=16%>...\n" + following["target"]
    add("context", before_source + "\n" + selected[0]["runtime_source"] + "\n" + selected[1]["runtime_source"] + "</indent>\n" + after_source,
        before_target + "\n" + selected[0]["target"] + "\n" + selected[1]["target"] + "</indent>\n" + after_target, origins)
    save(ROOT / "translation/supplemental/ghost-farewell-tests.json", cases)
    save(ROOT / "runtime/build/ghost-farewell/source-audit.json", {
        "selected": selected, "sharing_audit": {"exact_dialogue_occurrences": 1,
            "italic_runtime_occurrences": 1, "all_textasset_substring_occurrences": substring_hits,
            "other_long_dialogue_occurrences_unchanged": 6},
    })
    print("10项真实裸句、斜体、对话框封套、日志及相邻语境消费者用例已生成")


if __name__ == "__main__":
    main()
