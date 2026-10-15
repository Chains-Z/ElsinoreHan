"""绑定真实密会称呼和日志姓名，生成消费者及TMP重放输入。"""

import base64
from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}
    selected = []
    for actor, identifier in (("fortinbras", "p09354-29b45c951150"), ("ophelia", "p01287-ff7ef393f145"),
                              ("brit", "p09341-610a72e9bb2b"), ("brit", "p09357-475e2296057b")):
        row = next(item for item in rows if item["actor"] == actor and item["id"] == identifier)
        assert any(origin["scene"] in {"Brit_Fortinbras_Ophelia", "FORT_SecretTownMeeting"} for origin in row["origins"])
        selected.append(row)
    assert selected[1]["target"] == "是，大人。"
    assert "Your Majesty" in selected[3]["source"] and "陛下" in selected[3]["target"]

    def speaker(row):
        name = short_name(row["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + row["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + row["target"])

    cases = []
    for index, row in enumerate(selected):
        for kind, source, target in (("leaf", row["runtime_source"], row["target"]), ("speaker", *speaker(row))):
            cases.append({"id": "log-speaker-" + str(index) + "-" + kind, "source": source, "target": target, "origins": row["origins"]})
    pair = [speaker(selected[index]) for index in (2, 1)]
    cases.append({"id": "log-speaker-instruction-reply", "source": "</indent>\n".join(item[0] for item in pair),
                  "target": "</indent>\n".join(item[1] for item in pair), "origins": selected[1]["origins"]})
    save(ROOT / "translation/supplemental/log-speaker-tests.json", cases)
    output = ROOT / "runtime/build/log-speaker"
    save(output / "source-audit.json", selected)
    encode = lambda value: base64.b64encode(value.encode("utf-8")).decode("ascii")
    (output / "cases.tsv").write_text("\n".join(str(index) + "\t" + encode(source) + "\t" + encode(target)
        for index, (source, target) in enumerate(speaker(row) for row in selected[:3])) + "\n", encoding="utf-8")
    print("9项真实消费者及3项真实资源日志排版重放输入已生成")


if __name__ == "__main__":
    main()
