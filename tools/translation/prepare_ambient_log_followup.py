"""核查全部对白及闲聊的日志封套，补齐真实格式器的尾段边界。"""

import base64
import hashlib
import json
import re
from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, assets = extract_rows(translations)
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}
    names = sorted({short_name(actor, mapping) for actor in mapping}, key=lambda value: (-len(value), value))
    names_union = "(?:" + "|".join(re.escape(name) for name in names) + ")"
    start = "<b>" + names_union + r":</b> <indent=16%>"
    origin = ["analysis/ui-audit/dialogue-log-followup-il.json:HistoryTracker.formatEntry",
              "resources.assets:name_mapping", "用户重开仍漏译的日志截图及真实保存记录，2026-10-15"]
    rules = [{"id": "ui-rule-log-orphan-indent-prefix", "priority": 71,
              "pattern": r"^(?<prefix_i>(?:</indent>)?\n)(?<body>" + start + r"[\s\S]+)\z$",
              "replacement": "${prefix_i}${body}", "origins": origin,
              "note": "真实formatEntry在前一发言仍存在而显示尾段的builder为空时，先追加结束缩进换行；仅接受真实姓名及日志缩进结构，未知正文仍须递归失败，不更换后续规则兜底"},
             {"id": "ui-rule-log-closed-indent-final-newline", "priority": 72,
              "pattern": r"^(?<body>" + start + r"[\s\S]+?)(?<close_i></indent>)(?<newline_i>\n)\z$",
              "replacement": "${body}${close_i}${newline_i}", "origins": origin,
              "note": "formatEntry从对白转到无显示文字的逻辑/舞台条目时仍先关闭缩进并换行；保护准确末尾格式，不泛化任意英文换行"}]
    save(ROOT / "translation/supplemental/ambient-log-followup-rules.json", rules)
    directory = ROOT / "runtime/build/ambient-log"
    cases, unresolved = [], []

    def speaker(row):
        source = row["runtime_source"]
        target = row["target"]
        if target is None:
            if re.search("[A-Za-z]", re.sub("<[^>]*>", "", source)):
                unresolved.append(row)
                return None
            target = source
        if row["target"] is not None and row["actor"] == "ghost" and source not in targets:
            target = "<i>" + target + "</i>"
        name = short_name(row["actor"], mapping)
        label = SPECIAL_NAMES.get(name) or targets.get(name, name)
        return ("<b>" + name + ":</b> <indent=16%>" + source,
                "<b>" + label + ":</b> <indent=16%>" + target)

    for index, row in enumerate(rows):
        if row["actor"] not in mapping:
            unresolved.append(row)
            continue
        pair = speaker(row)
        if pair is None:
            continue
        for kind, prefix, suffix in (("normal", "", ""), ("tail", "</indent>\n", ""),
                                     ("closed", "", "</indent>\n")):
            cases.append({"id": "ambient-all-" + str(index) + "-" + kind,
                          "source": prefix + pair[0] + suffix, "target": prefix + pair[1] + suffix})
    for offset in range(0, len(cases), 1500):
        save(directory / ("all-cases-" + str(offset // 1500) + ".json"), cases[offset:offset + 1500])

    def get(actor, source):
        return next(row for row in rows if row["actor"] == actor and row["source"] == source)

    sequence = [get("marcellus", "A' course, Cap'n."), get("bernardo", "Good. Dismissed."),
                get("ophelia", "That's the herald's horn."), get("ophelia", "This is an unusual time for an announcement.")]
    source, target = "", ""
    previous = "kubilius"
    runtime = []
    for index, row in enumerate(sequence):
        pair = speaker(row)
        if previous == row["actor"]:
            source += "\n" + row["runtime_source"]
            target += "\n" + row["target"]
        else:
            source += "</indent>\n" + pair[0]
            target += "</indent>\n" + pair[1]
        previous = row["actor"]
        runtime.append({"id": "summons-tail-prefix-" + str(index + 1), "source": source, "target": target,
                        "origins": [origin for part in sequence[:index + 1] for origin in part["origins"]]})
    representative = runtime + [{"id": "summons-tail-line-height", "source": "<line-height=90%>" + source,
                                  "target": "<line-height=90%>" + target, "origins": origin},
        {"id": "summons-tail-closed", "source": source + "</indent>\n", "target": target + "</indent>\n", "origins": origin},
        {"id": "summons-tail-unknown-body", "source": "</indent>\n<b>Marcellus:</b> <indent=16%>Unreviewed marker.", "target": None, "origins": origin},
        {"id": "summons-tail-unknown-name", "source": "</indent>\n<b>UnknownActor:</b> <indent=16%>Good. Dismissed.", "target": None, "origins": origin}]
    save(ROOT / "translation/supplemental/ambient-log-tests.json", representative)
    enc = lambda value: base64.b64encode(value.encode("utf-8")).decode("ascii")
    (directory / "cache-cases.tsv").write_text("".join(row["id"] + "\t" + enc(row["source"]) + "\t" + enc(row["target"]) + "\n"
        for row in representative if row["target"] is not None), encoding="utf-8")
    save(directory / "formatter-case.json", {"previous": {"actor": "kubilius", "source": "Aye, Captain."},
        "entries": [{"actor": row["actor"], "source": row["runtime_source"]} for row in sequence],
        "expected_source": source, "expected_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest()})
    (directory / "formatter-case.tsv").write_text(
        "previous\tkubilius\t" + enc("Aye, Captain.") + "\n" +
        "".join("entry\t" + row["actor"] + "\t" + enc(row["runtime_source"]) + "\n" for row in sequence) +
        "expected\t\t" + enc(source) + "\n", encoding="utf-8")
    save(directory / "source-audit.json", {"assets": assets, "unique_actor_dialogues": len(rows), "all_case_count": len(cases),
        "batch_count": (len(cases) + 1499) // 1500, "unresolved": unresolved,
        "screenshot_rows": sequence, "source_kind": "全部TextAsset真实发言及格式器可产生边界，不代表所有剧情已游玩"})
    print(json.dumps({"unique_actor_dialogues": len(rows), "all_cases": len(cases), "unresolved": len(unresolved), "rules": 2}))


if __name__ == "__main__":
    main()
