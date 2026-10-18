"""绑定真实谢幕对白，生成四万个兄弟校订的离线消费者用例。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, digest, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    row = next(item for item in rows if item["id"] == "p06318-d1a781768d22")
    assert row["actor"] == "hamlet"
    assert row["source"] == row["runtime_source"]
    assert row["source_sha256"] == "d1a781768d2204f15005b2d443481333aef6673efd31f8a453b5f7a34ba65b6b"
    assert row["target"] == "<b>四万</b>个兄弟的爱加在一起，也抵不过我的爱——"
    assert row["origins"] == [{"asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
                               "scene": "END_CurtainCall_Resignation", "line": 17134}]
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + item["target"])

    context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
    # 同一人物连续发言先换行，换人物才结束indent，沿用真实日志消费者结构。
    combined_source = context[1][0] + "\n" + row["runtime_source"]
    combined_target = context[1][1] + "\n" + row["target"]
    cases = []
    for kind, source, target in (
        ("leaf", row["runtime_source"], row["target"]),
        ("dialogue", "<line-height=90%>" + row["runtime_source"], "<line-height=90%>" + row["target"]),
        ("speaker", *speaker(row)),
        ("same-speaker", combined_source, combined_target),
        ("context", context[0][0] + "</indent>\n" + combined_source + "</indent>\n" + context[3][0],
         context[0][1] + "</indent>\n" + combined_target + "</indent>\n" + context[3][1]),
    ):
        cases.append({"id": "hamlet-brothers-" + kind, "source": source, "target": target,
                      "source_sha256": digest(source), "origins": row["origins"]})
    save(ROOT / "translation/supplemental/hamlet-brothers-tests.json", cases)
    save(ROOT / "runtime/build/hamlet-brothers/source-audit.json", row)
    print("5项真实裸句、对话框封套、日志单句、连续发言及相邻语境消费者用例已生成")


if __name__ == "__main__":
    main()
