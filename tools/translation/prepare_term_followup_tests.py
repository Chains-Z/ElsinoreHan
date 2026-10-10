"""生成时间线状态及宗教类别校订的实际消费者用例，不改游戏条件。"""

import json
from prepare_dialogue_log_followup import ROOT, read, save


def main():
    directory = ROOT / "translation/supplemental"
    labels = read(directory / "timeline-label-corrections.json")
    terms = read(directory / "religious-term-corrections.json")
    cases = [{"id": row["id"] + "-leaf", "source": row["source"], "target": row["target"],
              "origins": row["origins"]} for row in labels + terms]
    translations = {r["source"]: r["target"] for r in read(ROOT / "translation/sol-full-2026-10-09/translations.json")}
    event = "Hamlet provides some suggestions for Quince's performance."
    for row in labels:
        source, target = row["source"] + event, row["target"].rstrip() + translations[event]
        for suffix, prefix in (("tooltip", ""), ("height", "<line-height=90%>")):
            cases.append({"id": row["id"] + "-" + suffix, "source": prefix + source, "target": prefix + target})
    speech = next(row for row in terms if row["original_id"] == "p07778-f5e993b6694f")
    source = "<b>Horatio:</b> <indent=16%>" + speech["source"]
    target = "<b>霍拉旭:</b> <indent=16%>" + speech["target"]
    cases.append({"id": "religious-horatio-log", "source": source, "target": target})
    notice = "<b>Ophelia</b> learns about multiple events.\n"
    cases.append({"id": "religious-horatio-notice-tail", "source": source + "</indent>\n" + notice,
                  "target": target + "</indent>\n<b>奥菲莉娅</b>得知了多个事件。\n"})
    save(directory / "term-followup-tests.json", cases)
    print(json.dumps({"cases": len(cases)}))


if __name__ == "__main__":
    main()
