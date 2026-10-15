"""从真实独白生成死亡如睡眠校订与相邻日志的消费者回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    selected = [row for row in rows if row["id"] == "p01401-bac2254636db"]
    assert len(selected) == 1
    row = selected[0]
    assert row["actor"] == "hamlet"
    assert row["target"] == "死去——不过是睡去，如此而已。而我说的睡眠，是让心痛终结，让我必须承受的千般细碎痛楚终结。"
    assert row["origins"] == [{
        "asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
        "scene": "Spine_ToBeOrNotToBe", "line": 1489,
    }]
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"]
               for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + targets[name] + ":</b> <indent=16%>" + item["target"])

    source, target = speaker(row)
    context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
    cases = [{"id": "hamlet-soliloquy-" + kind, "source": source, "target": target, "origins": row["origins"]}
             for kind, source, target in (
                 ("leaf", row["runtime_source"], row["target"]), ("speaker", source, target),
                 ("context", "</indent>\n".join(part[0] for part in context),
                  "</indent>\n".join(part[1] for part in context)))]
    save(ROOT / "translation/supplemental/hamlet-soliloquy-tests.json", cases)
    save(ROOT / "runtime/build/hamlet-soliloquy/source-audit.json", selected)
    print("3项独白裸句、角色日志与真实相邻语境用例已生成")


if __name__ == "__main__":
    main()
