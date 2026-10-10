"""验证负向事件通知的实际模板、弹窗及日志衔接，不把内部条件当译文。"""

import itertools
import json
from pathlib import Path

from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save


def main():
    full = ROOT / "translation/sol-full-2026-10-09"
    targets = {r["source"]: r["target"] for r in read(full / "translations.json")}
    pattern = "<b>Ophelia</b> no longer has this future event on her <b>Timeline</b>: %s"
    descriptions = [
        "The esteemed Peter Quince will be performing one of his odd one-man plays with Hamlet's help.",
        "Quince puts on a play about Gertrude's affair.",
        "Quince puts on a play about the Spy.",
        "Quince puts on a play about Hamlet.",
        "Quince puts on a play about my predicament.",
    ]
    atoms = [(pattern.replace("%s", d), targets[pattern].replace("%s", targets[d])) for d in descriptions]
    for source in (
        "<b>Ophelia</b> no longer has a future event on her <b>Timeline</b>.",
        "<b>Ophelia</b> no longer has multiple future events on her <b>Timeline</b>.",
    ):
        atoms.append((source, targets[source]))
    cases = []

    def add(kind, source, target):
        cases.append({"id": "invited-notice-" + kind + "-" + str(len(cases)),
                      "source": source, "target": target})

    add("door", "Out to Sea", targets["Out to Sea"])
    padding = "\n<line-height=40%>\n<line-height=90%>"
    for source, target in atoms:
        add("leaf", source, target)
        add("tail", source + "\n", target + "\n")
        add("popup", "<line-height=90%>" + source + padding,
            "<line-height=90%>" + target + padding)
    notifications = read(ROOT / "translation/supplemental/notification-list-atoms.json")
    # 复用全部既有真实格式通知，验证新通知前后都不会卡住正常消息。
    for source, target in atoms:
        for row in notifications:
            for left, right in (((source, target), (row["source"], row["target"])),
                                ((row["source"], row["target"]), (source, target))):
                add("notice-pair", left[0] + "\n" + right[0] + "\n",
                    left[1] + "\n" + right[1] + "\n")
    names = sorted(set(read(ROOT / "analysis/ui-audit/dialogue-log-source-audit.json")["short_names"].values()))
    for name in names:
        target_name = name if name == "???" else SPECIAL_NAMES.get(name) or targets[name]
        speech = "<b>" + name + ":</b> <indent=16%>Dinner is served."
        translated = "<b>" + target_name + ":</b> <indent=16%>" + targets["Dinner is served."]
        for source, target in atoms:
            add("speech-before", speech + "</indent>\n" + source + "\n",
                translated + "</indent>\n" + target + "\n")
            add("speech-after", source + "\n" + speech, target + "\n" + translated)
    for left, right in itertools.product(atoms, repeat=2):
        add("new-pair", left[0] + "\n" + right[0] + "\n", left[1] + "\n" + right[1] + "\n")
    build = ROOT / "runtime/build/invited-followup"
    build.mkdir(parents=True, exist_ok=True)
    save(build / "consumer-tests.json", cases)
    save(ROOT / "translation/supplemental/invited-notice-tests.json", cases[:22])
    print(json.dumps({"cases": len(cases), "new_atoms": len(atoms), "speaker_names": len(names),
                      "prior_notification_atoms": len(notifications)}))


if __name__ == "__main__":
    main()
