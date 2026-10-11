"""从真实对白再生幽灵短答、暴行语境与游戏比喻的定向消费者回归。"""

import json
import re

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    selected = [row for row in rows if row["source"].strip() == "I do."
                or "Terrible, bloody deeds were committed." in row["source"]
                or row["source"] == "It is impossible, yes. It is the rules of the larger game."]
    # 按真实出现位置检查，防止只改幽灵后遗留同形短句的错误解释。
    assert {row["actor"] for row in selected if row["source"] == "I do."} == {
        "brit", "ghost", "rosencrantz", "hamlet", "ophelia"}
    mapping_rows = read(ROOT / "analysis/ui-audit/resource-strings.json")
    mapping = {row["origin"]["field"]: row["source"] for row in mapping_rows
               if row["origin"].get("asset") == "name_mapping"}
    by_actor_source = {(row["actor"], row["source"]): row for row in rows}

    def speaker(row):
        name = short_name(row["actor"], mapping)
        target_name = SPECIAL_NAMES.get(name) or targets[name]
        target = row["target"]
        if target is None:
            assert not re.search(r"[A-Za-z]", re.sub(r"<[^>]*>", "", row["runtime_source"]))
            target = row["runtime_source"]
        return ("<b>" + name + ":</b> <indent=16%>" + row["runtime_source"],
                "<b>" + target_name + ":</b> <indent=16%>" + target)

    cases = []
    for index, row in enumerate(selected):
        assert row["target"] is not None
        if row["source"] == "I do.":
            assert row["target"] == ("<i>是的，我也一样。</i>" if row["actor"] == "ghost" else "是的。")
        if row["source"] == "It is impossible, yes. It is the rules of the larger game.":
            assert row["target"] == "<i>是的，那不可能。这是一场更大的游戏的规则。</i>"
            assert targets[row["source"]] == "是的，那不可能。这是一场更大的游戏的规则。"
            cases.append({"id": "ghost-larger-game-bare", "source": row["source"],
                          "target": targets[row["source"]], "origins": row["origins"]})
        source, target = speaker(row)
        contexts = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
        for kind, source, target in (
            ("leaf", row["runtime_source"], row["target"]),
            ("speaker", source, target),
            ("context", "</indent>\n".join(part[0] for part in contexts),
             "</indent>\n".join(part[1] for part in contexts)),
        ):
            cases.append({"id": f"ghost-context-{index}-{kind}", "source": source,
                          "target": target, "origins": row["origins"]})
    save(ROOT / "translation/supplemental/ghost-context-tests.json", cases)
    save(ROOT / "runtime/build/ghost-context/source-audit.json", selected)
    print(json.dumps({"reviewed_actor_sources": len(selected), "cases": len(cases)}))


if __name__ == "__main__":
    main()
