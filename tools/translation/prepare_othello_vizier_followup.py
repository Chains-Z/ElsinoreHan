"""从真实奥赛罗对白再生高级大臣称谓与相邻语境消费者回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    selected = [row for row in rows if "one of the Sultan's own viziers" in row["source"]]
    assert len(selected) == 1 and selected[0]["actor"] == "othello"
    row = selected[0]
    assert "苏丹麾下的一名高级大臣" in row["target"] and "维齐尔" not in row["target"]
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + targets[name] + ":</b> <indent=16%>" + item["target"])

    source, target = speaker(row)
    context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
    cases = [{"id": "othello-vizier-" + kind, "source": source, "target": target, "origins": row["origins"]}
             for kind, source, target in (
                 ("leaf", row["runtime_source"], row["target"]), ("speaker", source, target),
                 ("context", "</indent>\n".join(part[0] for part in context),
                  "</indent>\n".join(part[1] for part in context)))]
    save(ROOT / "translation/supplemental/othello-vizier-tests.json", cases)
    save(ROOT / "runtime/build/othello-vizier/source-audit.json", selected)
    print("3项高级大臣称谓与真实相邻语境用例已生成")


if __name__ == "__main__":
    main()
