"""从真实独白、憎恨比喻及船上争论生成定向对白消费者回归。"""

import re

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    for row in rows:
        if row["target"] is None:
            # 无词汇的停顿按真实源保留，未知英文不得借此绕过缺译检查。
            if not re.search("[A-Za-z]", re.sub("<[^>]*>", "", row["runtime_source"])):
                row["target"] = row["runtime_source"]
    expected = {
        "p01397-d66f4bbd3a6f": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1480]),
        "p01398-278e713c8a99": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1481]),
        "p01399-44b99c899e19": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1484]),
        "p01400-5af5343a778d": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1486]),
        "p01401-bac2254636db": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1489]),
        "p01402-938308c47843": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1491]),
        "p01403-07f57b1f3827": ("soliloquy", "hamlet", "Spine_ToBeOrNotToBe", [1494]),
        "p04895-16b2765c8599": ("social", "laertes", "BOYS_Meeting4", [12769, 12777]),
        "p05384-9448400f6ab9": ("social", "hamlet", "PIRATE_GuildAndHamlet", [14196]),
        "p05389-a41d610348f3": ("social", "hamlet", "PIRATE_GuildAndHamlet", [14209]),
        "p05390-f4645159eb19": ("social", "hamlet", "PIRATE_GuildAndHamlet", [14210]),
        "p05391-6df9700c78c0": ("social", "ophelia", "PIRATE_GuildAndHamlet", [14212]),
        "p05392-60062c417e4f": ("social", "hamlet", "PIRATE_GuildAndHamlet", [14214]),
        "p05393-7bf7721fe7d0": ("social", "guildenstern", "PIRATE_GuildAndHamlet", [14217]),
        "p05394-4a4c780cc262": ("social", "guildenstern", "PIRATE_GuildAndHamlet", [14219]),
        "p05395-e91ec703d462": ("social", "guildenstern", "PIRATE_GuildAndHamlet", [14220]),
        "p05398-60df77082ce8": ("social", "guildenstern", "PIRATE_GuildAndHamlet", [14226]),
        "p05399-310ea68d3af2": ("social", "guildenstern", "PIRATE_GuildAndHamlet", [14228]),
        "p05400-7d4fdbccd434": ("social", "guildenstern", "PIRATE_GuildAndHamlet", [14229]),
        "p05440-5d60845a6f70": ("social", "grace", "PIRATE_GraceAttack", [14367]),
        "p05441-6889e3eb71db": ("social", "grace", "PIRATE_GraceAttack", [14368]),
        "p05445-f8fdc8f5d77d": ("social", "grace", "PIRATE_GraceAttack", [14379]),
    }
    # 提取器优先选择实际运行别名，审校范围仍绑定真实脚本文字对应的正文ID。
    source_ids = {row["source"]: row["id"] for row in translations}
    selected = [{**row, "runtime_entry_id": row["id"], "id": source_ids[row["source"]]}
                for row in rows if source_ids.get(row["source"]) in expected]
    assert len(selected) == len(expected)
    corrections = {row["id"]: row for row in read(ROOT / "translation/sol-full-2026-10-09/local-corrections.json")}
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"]
               for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + item["target"])

    suites = {"soliloquy": [], "social": []}
    for row in selected:
        suite, actor, scene, lines = expected[row["id"]]
        assert row["actor"] == actor
        assert row["origins"] == [{
            "asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
            "scene": scene, "line": line,
        } for line in lines]
        if row["id"] in corrections:
            assert row["target"] == corrections[row["id"]]["corrected_target"]
        assert targets[row["runtime_source"]] == row["target"]
        source, target = speaker(row)
        context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
        suites[suite].extend({"id": "hamlet-" + row["id"] + "-" + kind,
                              "source": source, "target": target, "origins": row["origins"]}
                            for kind, source, target in (
                                ("leaf", row["runtime_source"], row["target"]), ("speaker", source, target),
                                ("context", "</indent>\n".join(part[0] for part in context),
                                 "</indent>\n".join(part[1] for part in context))))
        if row["source"] != row["runtime_source"]:
            suites[suite].append({"id": "hamlet-" + row["id"] + "-canonical",
                                  "source": row["source"], "target": row["target"], "origins": row["origins"]})

    def group_content(group):
        source, target, previous = "", "", None
        for item in group:
            if previous and previous["actor"] == item["actor"]:
                source += "\n" + item["runtime_source"]
                target += "\n" + item["target"]
            else:
                english, chinese = speaker(item)
                source += ("</indent>\n" if previous else "") + english
                target += ("</indent>\n" if previous else "") + chinese
            previous = item
        return source, target

    soliloquy = sorted((row for row in selected if expected[row["id"]][0] == "soliloquy"),
                       key=lambda row: row["origins"][0]["line"])
    source, target = group_content(soliloquy)
    suites["soliloquy"].append({"id": "hamlet-soliloquy-complete", "source": source, "target": target,
                                "origins": [origin for row in soliloquy for origin in row["origins"]]})
    # 此段没有互斥对白，按真实顺序以八条为一组验证完整争论。
    argument = sorted(({**row, "origins": [origin]} for row in rows for origin in row["origins"]
                       if origin["scene"] == "PIRATE_GuildAndHamlet" and 14184 <= origin["line"] <= 14245),
                      key=lambda row: row["origins"][0]["line"])
    for index in range(0, len(argument), 8):
        group = argument[index:index + 8]
        source, target = group_content(group)
        suites["social"].append({"id": "hamlet-argument-block-" + str(index // 8), "source": source, "target": target,
                                 "origins": [origin for row in group for origin in row["origins"]]})
    save(ROOT / "translation/supplemental/hamlet-soliloquy-tests.json", suites["soliloquy"])
    save(ROOT / "translation/supplemental/hamlet-social-dialogue-tests.json", suites["social"])
    save(ROOT / "runtime/build/hamlet-soliloquy/source-audit.json", selected)
    print("独白%d项、比喻与船上争论%d项真实消费者用例已生成" % (len(suites["soliloquy"]), len(suites["social"])))


if __name__ == "__main__":
    main()
