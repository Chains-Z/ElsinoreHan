"""从真实资源再生贝尔纳多回应友谊承诺的定向消费者回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    selected = [row for row in rows if row["source"] == "There's that, at least."]
    assert len(selected) == 1 and selected[0]["actor"] == "bernardo"
    row = selected[0]
    assert row["target"] == "至少，我还有你这个朋友。"
    assert row["context"][1]["source"] == (
        "What you choose to tell others is up to you. But I will always—<i>always</i> be your friend.")
    mapping = {item["origin"]["field"]: item["source"]
               for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + targets[name] + ":</b> <indent=16%>" + item["target"])

    source, target = speaker(row)
    context = [speaker(by_actor_source[(part["actor"], part["source"])])
               for part in row["context"]]
    notice = "<b>Ophelia</b> learns about an event.\n"
    cases = [{"id": "bernardo-friend-" + kind, "source": source, "target": target,
              "origins": row["origins"]} for kind, source, target in (
        ("leaf", row["runtime_source"], row["target"]),
        ("speaker", source, target),
        ("context", "</indent>\n".join(part[0] for part in context),
         "</indent>\n".join(part[1] for part in context)),
        ("notice-before", notice + source, targets[notice] + target),
        ("notice-after", source + "</indent>\n" + notice,
         target + "</indent>\n" + targets[notice]),
    )]
    save(ROOT / "translation/supplemental/bernardo-friend-tests.json", cases)
    save(ROOT / "runtime/build/bernardo-friend/source-audit.json", selected)
    print("真实语境与5项消费者用例已生成")


if __name__ == "__main__":
    main()
