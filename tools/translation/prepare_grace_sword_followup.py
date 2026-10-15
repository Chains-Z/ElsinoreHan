"""从真实格蕾丝对白生成打斗语境及人命语序的消费者回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    row = next(row for row in rows if row["id"] == "p08751-b3c5b792c58b")
    assert row["actor"] == "grace"
    assert row["target"] == "不过，你比大多数人都娇小些——恐怕得退而求其次，教你给对手添点麻烦，还谈不上让你成为多大的威胁。"
    assert row["origins"] == [{"asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
                               "scene": "GRACE_SwordLesson", "line": 24491}]
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + item["target"])

    source, target = speaker(row)
    context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
    cases = [{"id": "grace-sword-" + kind, "source": source, "target": target, "origins": row["origins"]}
             for kind, source, target in (("leaf", row["runtime_source"], row["target"]), ("speaker", source, target),
                 ("context", "</indent>\n".join(part[0] for part in context), "</indent>\n".join(part[1] for part in context)))]
    death = next(item for item in rows if item["id"] == "p08933-603a5ec7100a")
    assert death["actor"] == "grace"
    assert death["target"] == "这些年我至少学会了一件事：闹出没必要的人命，迟早总会给我惹来麻烦。"
    assert death["origins"] == [{"asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
                                  "scene": "GRACE_PostMutinyNoDeath", "line": 24879}]
    source, target = speaker(death)
    cases.extend({"id": "grace-death-" + kind, "source": source, "target": target, "origins": death["origins"]}
                 for kind, source, target in (("leaf", death["runtime_source"], death["target"]), ("speaker", source, target)))
    save(ROOT / "translation/supplemental/grace-sword-tests.json", cases)
    save(ROOT / "runtime/build/grace-sword/source-audit.json", [row, death])
    print("5项格蕾丝对白裸句、日志及真实语境消费者用例已生成")


if __name__ == "__main__":
    main()
