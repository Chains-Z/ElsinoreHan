"""绑定海盗分支幽灵的逃离与悔恨，核查真实双源及相邻连续发言消费者。"""

from audit_dialect_dialogue import extract_rows
from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import ROOT, digest, read, save


def main():
    directory = ROOT / "translation/supplemental"
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row for row in translations}
    changes = read(directory / "ghost-regret-corrections.json")
    checked = apply_supplemental([
        {"id": row["original_id"], "source": row["source"], "target": row["previous_target"]}
        for row in changes], changes)
    dialogue, _ = extract_rows(translations)
    row = next(row for row in dialogue if row["source"] == changes[0]["source"])
    assert row["actor"] == "ghost" and row["origins"][0]["scene"] == "END_CurtainCall_Pirate"
    assert {entry["source"] for entry in changes} == {row["source"], row["runtime_source"]}
    cases = []
    for entry in checked:
        assert entry["target"] == targets[entry["source"]]["target"]
        cases.append({"id": entry["id"], "source": entry["source"], "target": entry["target"],
                      "source_sha256": digest(entry["source"]), "origins": row["origins"]})
    source, target = row["runtime_source"], targets[row["runtime_source"]]["target"]
    assert target == "<i>" + targets[row["source"]]["target"] + "</i>"
    previous = row["context"][1]
    assert previous["actor"] == "ghost"
    previous_source = "<i>" + previous["source"] + "</i>"
    previous_target = targets[previous_source]["target"]
    for kind, text, translated in (
        ("box", "<line-height=90%>" + source, "<line-height=90%>" + target),
        ("speaker", "<b>Ghost:</b> <indent=16%>" + source, "<b>幽灵:</b> <indent=16%>" + target),
        ("same-speaker", "<b>Ghost:</b> <indent=16%>" + previous_source + "\n" + source,
         "<b>幽灵:</b> <indent=16%>" + previous_target + "\n" + target),
    ):
        cases.append({"id": "ghost-regret-" + kind, "source": text, "target": translated,
                      "source_sha256": digest(text), "origins": row["origins"]})
    save(directory / "ghost-regret-tests.json", cases)
    print("2条真实资源／斜体旧译覆盖及5项正文、对话框、单句日志和连续发言用例已核对")


if __name__ == "__main__":
    main()
