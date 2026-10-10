"""复用完整源审计与冻结正文，制备有来源的界面补译和动态拆分规则。"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "translation/sol-full-2026-10-09"
AUDIT = ROOT / "analysis/ui-audit"
OUT = ROOT / "translation/supplemental"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    manifest = read(FULL / "manifest.json")
    excluded = {r["id"] for r in read(FULL / "excluded-nontext.json")}
    targets = {r["id"]: r["target"] for batch in manifest["batches"] for r in read(FULL / "outputs" / (batch["id"] + ".json"))["translations"]}
    base = {r["source"]: targets[r["id"]] for r in manifest["entries"] if r["id"] not in excluded}
    entries = {}
    def add(source, target, origins, kind, **extra):
        if source in entries:
            if entries[source]["target"] != target:
                raise ValueError("补译来源产生冲突：" + source)
            entries[source]["origins"] += origins
            return
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        row = {"id": "ui-" + digest[:16], "source": source, "target": target, "source_sha256": digest,
               "origins": origins, "kind": kind, "translation_method": "本会话Sol定向补译或明确记录的冻结译文复用，无新增API调用", **extra}
        if source in base: row["previous_target"] = base[source]
        entries[source] = row
    settings = {"Normal":"正常", "Faster":"较快", "Fastest":"最快", "Instant":"立即显示", "Default":"默认", "Modern":"现代", "Low":"低", "Medium":"中", "High":"高", "Windowed":"窗口", "Borderless":"无边框", "Fullscreen":"全屏", "Native":"原生分辨率"}
    for source, target in settings.items():
        add(source, target, ["translation/supplemental/settings-option-sources.json"], "settings_option")
    for name in ("assembly-ui-candidates.json", "resource-ui-candidates.json"):
        for row in read(AUDIT / name):
            if row["source"] in entries: continue
            assert hashlib.sha256(row["source"].encode()).hexdigest() == row["source_sha256"]
            add(row["source"], row["suggested_target"], [{"audit": "analysis/ui-audit/" + name, "source_sha256": row["source_sha256"]}], "audited_ui")
            if "%%" in row["source"] and any("Printf" in str(u.get("context", "")) for u in row.get("usages", [])):
                add(row["source"].replace("%%", "%"), row["suggested_target"].replace("%%", "%"), ["analysis/ui-audit/" + name], "printf_literal_percent")
    for row in read(AUDIT / "assembly-existing-aliases.json"):
        add(row["source"], row["target"], [{"audit":"analysis/ui-audit/assembly-existing-aliases.json", "existing_id":row["existing_id"]}], "frozen_dialogue_format_alias")
    evidence = read(AUDIT / "dynamic-ui-sources.json")
    including_pattern = next(r["pattern"] for r in evidence["recommended_splitters"] if r["id"] == "including")
    union = re.search(r"\(\?:([^()]+)\)", including_pattern)[1]
    names = [re.sub(r"\\(.)", r"\1", n) for n in union.split("|")]
    glossary = {r["source"]: r["target"] for r in read(FULL / "glossary.json")["entries"]}
    for name in names:
        if name != "???" and name not in base and name not in entries:
            add(name, glossary[name], ["analysis/ui-audit/dynamic-ui-sources.json", "translation/sol-full-2026-10-09/glossary.json"], "frozen_name")
    save(OUT / "ui-translations.json", list(entries.values()))
    rooms = sorted({r["source"] for r in read(AUDIT / "resource-ui-candidates.json") if "room_name" in r["categories"]}, key=len, reverse=True)
    room = "(?:" + "|".join(map(re.escape, rooms)) + ")"
    days = "(?:Wednesday|Thursday|Friday|Saturday|Sunday)"
    clock = r"(?:[01]?[0-9]|2[0-3]):[0-5][0-9]"
    when = "(?:" + days + ", " + clock + "|Wednesday|Epilogue)"
    rules = []
    def rule(identifier, pattern, replacement):
        rules.append({"id":"ui-rule-"+identifier, "pattern":pattern[:-1] + r"\z$", "replacement":replacement, "origins":["analysis/ui-audit/dynamic-ui-sources.json"]})
    rule("clock", "^(?<day>" + days + "), (?<clock_i>" + clock + ")$", "${day} ${clock_i}")
    rule("location", "^(?<room>" + room + ")(?<bullet_i> •)$", "${room}${bullet_i}")
    rule("paragraph", r"^(?<left>[\s\S]+?)(?<separator_i>\n?<line-height=40%>\n<line-height=90%>)(?<right>[\s\S]+)$", "${left}${separator_i}${right}")
    rule("line-height", r"^(?<tag_i><line-height=90%>)(?<body>[\s\S]+)$", "${tag_i}${body}")
    rule("bold", r"^(?<open_i><b>)(?<body>[^<>]+)(?<close_i></b>)$", "${open_i}${body}${close_i}")
    for prefix, target in (("Future event:", "未来事件："), ("Unlikely event:", "当前条件下不会发生的事件："), ("Impossible event:", "未发生的事件：")):
        rule("prefix-" + prefix.split()[0].lower(), "^" + re.escape(prefix) + r" (?<event>[\\s\\S]+)$", target + "${event}")
    rule("opener", "^(?<when>" + when + " in " + room + r"), <i>in which</i> (?<event>[\\s\\S]+)$", "${when}，<i>事件：</i>${event}")
    rule("opener-bold", "^(?<when><b>" + when + " in " + room + r"</b>), <i>in which</i> (?<event>[\\s\\S]+)$", "${when}，<i>事件：</i>${event}")
    rule("opener-no-room", "^(?<when>" + when + r"), <i>in which</i> (?<event>[\\s\\S]+)$", "${when}，<i>事件：</i>${event}")
    rule("time-and-room", "^(?<when>" + when + ") in (?<room>" + room + ")$", "${when}，${room}")
    rule("including", including_pattern, "参与者：${people}。")
    name_rules = {"names_two":"${first}和${last}", "names_final":"和${last}"}
    person = "(?:" + union + ")"
    rule("names-oxford", "^(?<first>" + person + "(?:, " + person + ")*), and (?<last>" + person + ")$", "${first}和${last}")
    rule("names-commas", "^(?<first>" + person + "), (?<rest>" + person + "(?:, " + person + ")*)$", "${first}、${rest}")
    for recommendation in evidence["recommended_splitters"]:
        if recommendation["id"] in name_rules:
            rule(recommendation["id"], recommendation["pattern"], name_rules[recommendation["id"]])
    bold_person = "<b>" + person + "</b>"
    people = "(?:" + bold_person + "(?: and " + bold_person + "|(?:, " + bold_person + ")+, and " + bold_person + ")?)"
    rule("npc-state", "^(?<name>(?:" + person + "|" + bold_person + r"))(?<state> \((?:Dead|Shattered|Upset|Busy)\))$", "${name}${state}")
    rule("bold-names-two", "^(?<first>" + bold_person + ") and (?<last>" + bold_person + ")$", "${first}和${last}")
    rule("bold-names-oxford", "^(?<first>" + bold_person + "(?:, " + bold_person + ")*), and (?<last>" + bold_person + ")$", "${first}和${last}")
    rule("bold-names-commas", "^(?<first>" + bold_person + "), (?<rest>" + bold_person + "(?:, " + bold_person + ")*)$", "${first}、${rest}")
    rule("outcome-title", r"^<b>Outcome:</b>\n(?<body>[\s\S]+)$", "<b>结果：</b>\n${body}")
    rule("outcome-title-trailing", r"^<b>Outcome:</b>\n(?<body>[\s\S]+?)(?<trailing_i>\n+)$", "<b>结果：</b>\n${body}${trailing_i}")
    # 只接受Model产生的加粗人物句式；未知谓词原样保留，不替换程序内部ID。
    action = r"(?:dies\.|die\.|(?:shatters|shatter) and will not recover\.|(?:becomes|become) upset but will recover overnight\.|(?:now|no longer) (?:wants|want|believes that|believe that) [^\r\n]+\.)"
    outcome_line = "(?:" + people + " " + action + ")"
    rule("outcome-lines", "^(?<left>" + outcome_line + ")(?<newline_i>\n)(?<right>" + outcome_line + "(?:\n" + outcome_line + ")*\n?)$", "${left}${newline_i}${right}")
    rule("outcome-final-newline", "^(?<body>" + outcome_line + ")(?<newline_i>\n)$", "${body}${newline_i}")
    for verb, target in ((r"(?:dies|die)\.", "死去了。"), (r"(?:shatters|shatter) and will not recover\.", "精神崩溃，无法恢复。"), (r"(?:becomes|become) upset but will recover overnight\.", "心烦意乱，但过一夜就会恢复。")):
        rule("outcome-state-"+str(len(rules)), "^(?<people>" + people + ") " + verb + "$", "${people}" + target)
    for prefix, target in (("now", "现在"), ("no longer", "不再")):
        for verb, chinese in (("(?:wants|want)", "想要"), ("(?:believes that|believe that)", "相信")):
            rule("outcome-belief-"+str(len(rules)), "^(?<people>" + people + ") " + prefix + " " + verb + r" (?<term>[^\r\n]+)\.$", "${people}" + target + chinese + "${term}。")
    rule("bio-updated", "^Ophelia learns more about (?<people>" + people + r")\. Their Character Bios? will be updated in the <b>Journal</b>\.$", "奥菲莉娅进一步了解了${people}。<b>笔记</b>中的人物资料会随之更新。")
    rule("gains-term", r"^Ophelia gains  (?<term>[^\r\n]+)\.$", "奥菲莉娅获得了${term}。")
    rule("loses-term", r"^Ophelia loses  (?<term>[^\r\n]+)\.$", "奥菲莉娅失去了${term}。")
    save(OUT / "dynamic-ui-rules.json", rules)
    save(OUT / "ui-supplement-summary.json", {"entries":len(entries), "new_sources":sum(s not in base for s in entries), "base_overrides":sum(entries[s]["target"]!=base[s] for s in entries if s in base), "rules":len(rules), "settings_options":len(settings), "frozen_dialogue_aliases":60})
    print(json.dumps({"supplemental":len(entries),"new_sources":sum(s not in base for s in entries),"rules":len(rules)}))

if __name__ == "__main__": main()
