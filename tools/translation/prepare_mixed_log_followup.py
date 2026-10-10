"""从真实日志格式分支生成混合条目规则及衔接矩阵，保留英文原始历史。"""

import itertools
import json
from pathlib import Path
import re

from export_sol_full import encode
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, digest, read, save

OUT = ROOT / "translation/supplemental"
FULL = ROOT / "translation/sol-full-2026-10-09"
BUILD = ROOT / "runtime/build/mixed-log-followup"


def main():
    translations = read(FULL / "translations.json")
    targets = {r["source"]: r["target"] for r in translations}
    audit = read(ROOT / "analysis/ui-audit/dialogue-log-source-audit.json")
    shorts = sorted(set(audit["short_names"].values()), key=lambda s: (-len(s), s))
    name_union = "(?:" + "|".join(re.escape(s) for s in shorts) + ")"
    speaker_start = "<b>" + name_union + r":</b> <indent=16%>"
    notifications = []
    for row in read(OUT / "notification-ui-tests.json"):
        if (row["id"].startswith(("notification-bare-", "notification-belief-quotes-", "notification-nested-belief-"))
                and row["target"] is not None and "\n" not in row["source"]
                and "<line-height=" not in row["source"]):
            notifications.append({"kind": "LogicChange", "source": row["source"], "target": row["target"]})
    event = "Father and the King plan to catch Hamlet."
    for row in translations:
        if (row["source"].startswith("<b>Ophelia</b> learns about")
                and "event" in row["source"] and "\n" not in row["source"]):
            notifications.append({"kind": "LogicChange", "source": row["source"].replace("%s", event),
                                  "target": row["target"].replace("%s", targets[event])})
    notifications.append({"kind": "LogicChange", "source": "King Hamlet was murdered", "target": targets["King Hamlet was murdered"]})
    # HOLDS可直接输出所有已审零参命题，逐个消费，不只验证一条代表句。
    notification_audit = read(ROOT / "analysis/ui-audit/notification-source-audit.json")
    for row in notification_audit["zero_parameter_display_audit"]:
        if row.get("frozen_translation_id") and row["source"] in targets:
            notifications.append({"kind": "LogicChange", "source": row["source"], "target": targets[row["source"]]})
    notifications = list({r["source"]: r for r in notifications}.values())
    # 三人以上的实际通知同样是 LogicChange 原子；不能用单人前缀代替名单语法。
    for row in read(OUT / "notification-list-atoms.json") if (OUT / "notification-list-atoms.json").exists() else []:
        notifications.append({"kind": "LogicChange", "source": row["source"], "target": row["target"]})
    notifications = list({r["source"]: r for r in notifications}.values())
    prior = next(r for r in read(OUT / "notification-ui-rules.json")
                 if r["id"] == "ui-rule-notification-line-boundary")
    # 复用已审全名、通知前缀及真实命题；不按任意英语行进行拆分。
    marker = r"[\s\S]*?)(?<newline_i>\n)"
    notification_start = "(" + prior["pattern"].split("^(?<first>(", 1)[1].split(marker, 1)[0]
    if marker not in prior["pattern"] or not notification_start.endswith(")"):
        raise ValueError("通知边界来源结构变化，需要重新审核")
    notification_start = "(?:" + notification_start + "|" + "|".join(re.escape(r["source"]) for r in notifications) + ")"
    entry_start = "(?:" + speaker_start + "|<i>|" + notification_start + ")"
    origins = ["analysis/ui-audit/dialogue-log-followup-il.json:HistoryTracker.formatEntry",
               "analysis/ui-audit/notification-source-audit.json",
               "resources.assets:name_mapping"]
    rules = [{"id": "ui-rule-mixed-log-notification-boundary", "priority": 66,
              "pattern": "^(?<first>" + notification_start + r"[^\r\n]*)(?<newline_i>\n)(?<rest>" + entry_start + r"[\s\S]*)\z$",
              "replacement": "${first}${newline_i}${rest}", "origins": origins,
              "note": "LogicChange后续可为对白、舞台/Alert或另一通知；每个捕获仍需独立完整翻译"},
             {"id": "ui-rule-mixed-log-notification-trailing", "priority": 41,
              "pattern": "^(?<body>" + notification_start + r"[^\r\n]*)(?<newline_i>\n)\z$",
              "replacement": "${body}${newline_i}", "origins": origins,
              "note": "覆盖真实formatEntry为全部LogicChange通知追加的尾LF，正文仍需完整消费"},
             {"id": "ui-rule-mixed-log-speaker-boundary", "priority": 51,
              "pattern": "^(?<left>" + speaker_start + r"[\s\S]+?)(?<boundary_i></indent>\n)(?<right>" + entry_start + r"[\s\S]*)\z$",
              "replacement": "${left}${boundary_i}${right}", "origins": origins,
              "note": "对白后所有实际非对白类型，包括不带人物粗体的裸命题；八块推进规则优先"},
             {"id": "ui-rule-mixed-log-italic-boundary", "priority": 53,
              "pattern": r"^(?<left><i>[\s\S]+?</i>)(?<newline_i>\n)(?<right>" + entry_start + r"[\s\S]*)\z$",
              "replacement": "${left}${newline_i}${right}", "origins": origins,
              "note": "Stage/Alert后衔接全类型，优先级低于完整斜体对白续行，保留唱词/幽灵的完整原子"}]
    header = next(r for r in read(OUT / "dialogue-log-followup-rules.json")
                  if r["id"] == "ui-rule-log-header-shortnames-followup")
    header_left = header["pattern"].split("(?<entries>", 1)[0]
    # 此房间在早期日志白名单遗漏，但真实RoomMarker与时间线已经确认其显示源。
    header_left = header_left.replace(r"Upper\ Hallway|", r"Gertrude's\ Chambers|Upper\ Hallway|")
    rules.append({"id": "ui-rule-mixed-log-header", "priority": 70,
                  "pattern": header_left + "(?<entries>" + entry_start + r"[\s\S]*)\z$",
                  "replacement": header["replacement"], "origins": origins,
                  "note": "日志头可以直接接任意真实条目类型，不能限定为有粗体姓名的通知"})
    block = "(?:" + speaker_start + r"[\s\S]+?</indent>|<i>[\s\S]+?</i>|" + notification_start + r"[^\r\n]*)"
    chunks = ["(?<part" + str(i) + ">" + block + ")(?<boundary" + str(i) + r"_i>\n)" for i in range(1, 9)]
    rules.append({"id": "ui-rule-mixed-log-eight-entries", "priority": 68,
                  "pattern": "^" + "".join(chunks) + "(?<rest>" + entry_start + r"[\s\S]*)\z$",
                  "replacement": "".join("${part" + str(i) + "}${boundary" + str(i) + "_i}" for i in range(1, 9)) + "${rest}",
                  "origins": origins, "note": "混合长记录一次八条推进，每条独立消费；未知原子拒绝，递归上限仍为64"})

    cases = []
    def add(identifier, source, target, category):
        cases.append({"id": identifier, "source": source, "target": target,
                      "source_sha256": digest(source), "target_sha256": digest(target) if target is not None else None,
                      "origins": origins, "category": category,
                      "verification_level": "真实资源和HistoryTracker格式分支组合；不代表相应剧情可同时发生"})

    def speech(name, source="Dinner is served.", actor=None):
        target_name = SPECIAL_NAMES.get(name) or targets.get(name, name)
        return {"kind": "Dialogue", "actor": actor or name,
                "source": "<b>" + name + ":</b> <indent=16%>" + source,
                "target": "<b>" + target_name + ":</b> <indent=16%>" + targets[source]}

    def join(items, target=False):
        result = ""
        previous = None
        for item in items:
            body = item["target" if target else "source"]
            if previous and previous["kind"] == "Dialogue":
                if item["kind"] == "Dialogue" and previous["actor"] == item["actor"]:
                    body = body.split("<indent=16%>", 1)[1]
                    result += "\n" + body
                    previous = item
                    continue
                result += "</indent>\n"
            result += body
            if item["kind"] != "Dialogue":
                result += "\n"
            previous = item
        return result

    stage = {"kind": "Stage", "source": "<i>Enter Hamlet.</i>", "target": "<i>" + targets["Enter "] + targets["Hamlet"] + ".</i>"}
    # AlertAction接收已翻译文本，按真实分支整体包斜体；与Stage保持独立类型。
    alert = {"kind": "Alert", "source": "<i>I don't think Quince cares about this information.</i>",
             "target": targets["<i>I don't think {0} cares about this information.</i>"].replace("{0}", targets["Quince"])}
    dialogue = speech("Bernardo", "I turn to the court with a more pressing matter.")
    event_atom = next(r for r in notifications if r["source"] == "<b>Ophelia</b> learns about multiple events.")
    kinds = [dialogue, event_atom, stage, alert]
    # 所有类型二元/三元衔接，另独立覆盖相同人物和不同人物。
    for size in (2, 3):
        for index, items in enumerate(itertools.product(kinds, repeat=size)):
            add("mixed-type-" + str(size) + "-" + str(index), join(items), join(items, True), "type_matrix")
    add("mixed-type-different-speakers", join([dialogue, speech("Hamlet"), dialogue]),
        join([dialogue, speech("Hamlet"), dialogue], True), "type_matrix")
    observed = [r for r in read(OUT / "dynamic-ui-tests.json") if r["id"].startswith("log-observed-history-")]
    headers = list({(r["source"].split("\n", 1)[0], r["target"].split("\n", 1)[0]) for r in observed})
    # Header的三类真实分支：Event、Present、Other，不能只检查事件标题。
    common_source = '<line-height=90%><b>Thursday, 07:40</b>, <i>in which</i> '
    common_target = '<line-height=90%><b>星期四 07:40</b>，<i>事件：</i>'
    present_source = 'Ophelia presents "I\'m In Danger" to Quince.'
    present_target = targets['Ophelia presents "{0}" to {1}.'].replace("{0}", targets["I'm In Danger"]).replace("{1}", targets["Quince"])
    headers += [(common_source + present_source, common_target + present_target),
                (common_source + 'Start of Loop', common_target + targets['Start of Loop'])]
    for source, target in sorted(headers):
        for item in kinds + notifications:
            add("mixed-header-" + str(len(cases)), source + "\n" + join([item]),
                target + "\n" + join([item], True), "header_matrix")
    # 三种ILoggableStageDirection：人物进出、资源舞台文字、观察文档标题。
    extra_stages = [{"kind": "Stage", "source": r["source"].rstrip("\n"), "target": r["target"].rstrip("\n")}
                    for r in read(OUT / "dynamic-ui-tests.json")
                    if r["id"] in {"log-stage-enter-into", "log-stage-direction-pair"}]
    observed_view_source = '<i>Ophelia looks at "Hamlet\'s Personal Journal."</i>'
    observed_view_target = '<i>奥菲莉娅查看“哈姆雷特的私人日记”。</i>'
    if not any(observed_view_source in r["source"] and observed_view_target in r["target"] for r in observed):
        raise ValueError("真实观察文档Stage源与已验目标不符")
    extra_stages.append({"kind": "Stage", "source": observed_view_source, "target": observed_view_target})
    for item in extra_stages:
        for other in kinds + notifications:
            for items in ([item, other], [other, item]):
                add("mixed-stage-" + str(len(cases)), join(items), join(items, True), "stage_matrix")
    for index, notify in enumerate(notifications):
        for name in shorts:
            item = speech(name)
            for direction, items in (("before", [notify, item]), ("after", [item, notify]),
                                     ("between", [item, notify, item])):
                add("mixed-name-" + str(index) + "-" + name + "-" + direction,
                    join(items), join(items, True), "all_shortnames")
        for other in (stage, alert, notifications[0]):
            for items in ([notify, other], [other, notify]):
                add("mixed-notify-" + str(index) + "-" + str(len(cases)), join(items), join(items, True), "notification_matrix")
    future = next(r for r in notifications if "a future event in which" in r["source"])
    second = speech("Bernardo", "My lord, I believe the possibility exists that someone disloyal to Denmark exists within this court, and they may wish to do you harm.")
    court = [future, dialogue, second, speech("Polonius", "You mean a <i>spy</i>?")]
    add("mixed-screenshot-future-bernardo", join(court), join(court, True), "screenshot")
    # 所有实际对白原子都与本次事件通知双向衔接，不仅检查几个代表句。
    for index, row in enumerate(audit["dialogues"]):
        item = {"kind": "Dialogue", "actor": row["actor"],
                "source": "<b>" + row["short_name"] + ":</b> <indent=16%>" + row["runtime_source"],
                "target": "<b>" + row["short_target"] + ":</b> <indent=16%>" + row["target"]}
        for direction, items in (("before", [future, item]), ("after", [item, future])):
            add("mixed-all-dialogue-" + str(index) + "-" + direction, join(items), join(items, True), "all_dialogues")
    for length in (9, 64, 180):
        items = [kinds[i % len(kinds)] for i in range(length)]
        add("mixed-long-" + str(length), join(items), join(items, True), "depth_stress")
    for bad in ("<b>UnknownActor:</b> <indent=16%>Dinner is served.",
                "<b>Bernardo:</b> <indent=16%>Unknown internal dialogue marker.",
                "Ophelia learns about an internal event marker.", "<i>Unknown internal stage marker.</i>"):
        add("mixed-reject-" + str(len(cases)), future["source"] + "\n" + bad, None, "negative")
        add("mixed-reject-long-" + str(len(cases)), join(kinds * 3) + bad, None, "negative")
    pairs = []
    for index, items in enumerate(itertools.product(notifications, repeat=2)):
        pairs.append({"id": "mixed-all-notification-pair-" + str(index), "source": join(items), "target": join(items, True),
                      "category": "notification_pairs", "origins": origins})
    for index, actors in enumerate(itertools.product(sorted(audit["short_names"]), repeat=2)):
        # 两个角色可能共享同一个简称；formatEntry按角色ID判断同人，不能按简称判断。
        items = [speech(audit["short_names"][actor], actor=actor) for actor in actors]
        pairs.append({"id": "mixed-all-speaker-pair-" + str(index), "source": join(items), "target": join(items, True),
                      "category": "speaker_pairs", "origins": origins})
    save(OUT / "mixed-log-rules.json", rules)
    # 真实消费者先查精确/Trim词表，再查规则；固定通知末尾LF不能靠Splitter恢复。
    # 只登记实际通知原子的精确LF形式，译文逐字复用并保留相同尾LF。
    terminal_aliases = []
    for atom in notifications:
        if atom["source"] not in targets:
            continue
        source = atom["source"] + "\n"
        terminal_aliases.append({"id": "mixed-log-terminal-" + digest(source)[:16],
                                 "source": source, "source_sha256": digest(source),
                                 "target": targets[atom["source"]] + "\n", "origins": origins,
                                 "base_source": atom["source"], "base_target_sha256": digest(targets[atom["source"]]),
                                 "note": "固定逻辑通知追加真实尾LF；除尾LF外逐字复用已有译文，不更改正文"})
    save(OUT / "mixed-log-translations.json", terminal_aliases)
    save(OUT / "mixed-log-tests.json", cases)
    save(OUT / "mixed-log-pair-tests.json", pairs)
    save(OUT / "mixed-log-representative-tests.json", [r for r in cases if r["category"] in {"type_matrix", "screenshot", "depth_stress", "negative"}])
    old_rules = read(FULL / "dynamic-rules.json")
    new_ids = {r["id"] for r in rules}
    rendered = [{**r, "kind": "recursive_ui_splitter", "encoded_line": encode('sr:"' + r["pattern"] + '"') + "=" + encode('"' + r["replacement"] + '"')} for r in rules]
    save(BUILD / "combined-rules.json", sorted([r for r in old_rules if r["id"] not in new_ids] + rendered, key=lambda r: r.get("priority", 0)))
    save(BUILD / "combined-translations.json", translations + [r for r in terminal_aliases if r["source"] not in targets])
    save(BUILD / "manifest.json", {"shortnames": shorts, "character_ids": len(audit["short_names"]),
                                     "notification_variants": len(notifications), "types": [r["kind"] for r in kinds],
                                     "case_count": len(cases), "pair_case_count": len(pairs),
                                     "categories": {key: sum(r["category"] == key for r in cases) for key in sorted({r["category"] for r in cases})}})
    print(json.dumps({key: value for key, value in read(BUILD / "manifest.json").items() if key != "shortnames"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
