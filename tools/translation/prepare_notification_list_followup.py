"""补齐真实多人名单在通知包装和混合日志边界中的识别，生成有限回归矩阵。"""

import base64
import itertools

from prepare_dialogue_log_followup import ROOT, read, save, digest

OUT = ROOT / "translation/supplemental"
BUILD = ROOT / "runtime/build/notification-group"


def people_pattern():
    """复用既有真实 NameMap 白名单；formatCharacters 分别给每人加粗。"""
    row = next(r for r in read(OUT / "dynamic-ui-rules.json")
               if r["id"] == "ui-rule-log-quoted-belief-29")
    person = row["pattern"].split("<b>", 1)[1].split("</b>", 1)[0]
    bold = "<b>" + person + "</b>"
    people = "(?:" + bold + "(?: and " + bold + "|(?:, " + bold + ")+, and " + bold + ")?)"
    return bold + " ", people + " "


def repair_rows(rows):
    old, new = people_pattern()
    wanted = {"ui-rule-notification-line-boundary", "ui-rule-notification-final-newlines",
              "ui-rule-notification-terminal-paragraph"}
    for row in rows:
        if row["id"] not in wanted:
            continue
        if row.get("list_boundary_revision") != 1:
            if old not in row["pattern"]:
                raise ValueError("通知边界源结构变化，需要重新审核：" + row["id"])
            row["pattern"] = row["pattern"].replace(old, new)
            row["list_boundary_revision"] = 1
            row["origins"].append("Elsinore.dll:Model.formatCharacters IL_0003..IL_00c3；formatGroupedLiterals IL_0152/IL_0160")
            row["note"] += "；边界接受真实单人、二人和三人以上 Oxford 名单，逗号不再阻断通知包装与日志拆分"
        elif new not in row["pattern"]:
            raise ValueError("多人通知边界修订结构不符")
    return rows


def repair_boundaries():
    save(OUT / "notification-ui-rules.json", repair_rows(read(OUT / "notification-ui-rules.json")))


def format_people(names, targets):
    """精确复现 Model.formatCharacters 的一人、二人和多人的标记/标点。"""
    source = ["<b>" + n + "</b>" for n in names]
    target = ["<b>" + (n if n == "???" else targets[n]) + "</b>" for n in names]
    if len(names) == 1:
        return source[0], target[0]
    if len(names) == 2:
        return " and ".join(source), "和".join(target)
    return ", ".join(source[:-1]) + ", and " + source[-1], "、".join(target[:-1]) + "和" + target[-1]


def build_cases(targets, mapping):
    names = sorted(set(mapping.values()), key=lambda n: (-len(n), n))
    cases, atoms = [], []
    origins = ["analysis/ui-audit/notification-source-audit.json:name_mapping/padding_source_evidence",
               "Elsinore.dll:Model.formatCharacters/formatGroupedLiterals",
               "Assembly-CSharp.dll:HistoryTracker.formatEntry/DialogueUI.onStartLogicChange"]
    def add(source, target, category):
        cases.append({"id": "notification-list-" + category + "-" + str(len(cases)),
                      "source": source, "target": target, "source_sha256": digest(source),
                      "category": category, "origins": origins})
    def speech(name, text):
        return ("<b>" + name + ":</b> <indent=16%>" + text,
                "<b>" + targets[name] + ":</b> <indent=16%>" + targets[text])
    before, bt = speech("Bernardo", "Right, my lord.")
    after, at = speech("Polonius", "My King, I also have a grievance!")
    padding = "\n<line-height=40%>\n<line-height=90%>"
    def variants(source, target, category):
        add(source, target, category)
        add(source + "\n", target + "\n", "tail")
        add("<line-height=90%>" + source + padding,
            "<line-height=90%>" + target + padding, "popup")
        add(before + "</indent>\n" + source + "\n" + after,
            bt + "</indent>\n" + target + "\n" + at, "mixed")
    # 角色在一人及二人名单的全部位置，以及三/四/五人名单的各位置覆盖。
    groups = [(n,) for n in names] + list(itertools.product(names, repeat=2))
    groups += [tuple(names[(i + j) % len(names)] for j in range(size))
               for size in (3, 4, 5) for i in range(len(names))]
    observed = ("Queen Gertrude", "Polonius", "King Claudius")
    groups += [observed]
    for group in groups:
        source_names, target_names = format_people(group, targets)
        verb = "believes" if len(group) == 1 else "believe"
        source = source_names + " now " + verb + ' that "Fortinbras will cross Denmark".'
        target = target_names + "现在相信“" + targets["Fortinbras will cross Denmark"] + "”。"
        variants(source, target, "belief_names")
    source_names, target_names = format_people(observed, targets)
    states = [(" now want to destroy King Claudius.", "现在想要毁掉克劳狄斯国王。"),
              (" no longer want to destroy King Claudius.", "不再想要毁掉克劳狄斯国王。"),
              (' no longer believe that "Fortinbras will cross Denmark".',
               "不再相信“" + targets["Fortinbras will cross Denmark"] + "”。"),
              (" die.", "死去了。"),
              (" shatter and will not recover.", "精神崩溃，无法恢复。"),
              (" become upset but will recover overnight.", "心烦意乱，但过一夜就会恢复。")]
    atoms.append({"source": source_names + ' now believe that "Fortinbras will cross Denmark".',
                  "target": target_names + "现在相信“" + targets["Fortinbras will cross Denmark"] + "”。"})
    for source_tail, target_tail in states:
        source, target = source_names + source_tail, target_names + target_tail
        variants(source, target, "state")
        atoms.append({"source": source, "target": target})
    source = "Ophelia learns more about " + source_names + ". Their Character Bios will be updated in the <b>Journal</b>."
    target = "奥菲莉娅进一步了解了" + target_names + "。<b>笔记</b>中的人物资料会随之更新。"
    variants(source, target, "bio")
    atoms.append({"source": source, "target": target})
    for left, right in itertools.product(atoms, repeat=2):
        add("<line-height=90%>" + left["source"] + padding + right["source"] + padding,
            "<line-height=90%>" + left["target"] + padding + right["target"] + padding, "popup_pairs")
    # 嵌套信念保留两层主体，不能把外层信念变成客观事实。
    nested = source_names + ' now believe that Hamlet believes that "Fortinbras will cross Denmark".'
    nt = target_names + "现在认为，哈姆雷特相信“" + targets["Fortinbras will cross Denmark"] + "”。"
    variants(nested, nt, "nested")
    for bad in [source_names + ' now believe that "Unknown internal proposition".',
                '<b>UnknownActor</b>, <b>Polonius</b>, and <b>King Claudius</b> now believe that "Fortinbras will cross Denmark".']:
        add("<line-height=90%>" + bad + padding, None, "reject")
        add(before + "</indent>\n" + bad + "\n" + after, None, "reject")
    return cases, atoms


def main():
    repair_boundaries()
    targets = {r["source"]: r["target"] for r in read(ROOT / "translation/sol-full-2026-10-09/translations.json")}
    mapping = read(ROOT / "analysis/ui-audit/notification-source-audit.json")["name_mapping"]["entries"]
    cases, atoms = build_cases(targets, mapping)
    save(OUT / "notification-list-followup-tests.json", cases)
    save(OUT / "notification-list-atoms.json", atoms)
    representatives = [r for r in cases if r["category"] in {"state", "bio", "nested", "reject"}]
    representatives += [r for r in cases if 'Queen Gertrude</b>, <b>Polonius</b>, and <b>King Claudius</b> now believe' in r["source"]]
    save(OUT / "notification-list-representative-tests.json", list({r["id"]: r for r in representatives}.values()))
    actual_names = '<b>Queen Gertrude</b>, <b>Polonius</b>, and <b>King Claudius</b>'
    runtime_cases = [r for r in cases if actual_names in r["source"] and r["target"] is not None
                     and r["category"] in {"popup", "mixed"}]
    runtime_cases += [r for r in cases if r["category"] == "popup_pairs"][:2]
    # 真实离线 API 可以接收这些源；不代表已解锁每个资源状态或相应剧情。
    def b64(value):
        return base64.b64encode(value.encode("utf-8")).decode("ascii")
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "runtime-cases.tsv").write_text("\n".join(
        r["id"] + "\t" + b64(r["source"]) + "\t" + b64(r["target"]) for r in runtime_cases
    ) + "\n", encoding="utf-8", newline="\n")
    save(BUILD / "manifest.json", {"count": len(cases), "name_count": len(set(mapping.values())),
         "atoms": len(atoms), "runtime_cases": len(runtime_cases),
         "scope": "有限真实名单语法、全部二人名字位置及多人数代表性位置；不是全部剧情 E2E"})
    print("多人通知回归用例：" + str(len(cases)))


if __name__ == "__main__":
    main()
