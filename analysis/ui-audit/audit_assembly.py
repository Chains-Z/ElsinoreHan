"""静态审核实际 ldstr 用途；不修改游戏或冻结正文译文。"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ENGLISH = re.compile(r"[A-Za-z]")


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def dialogue_match_key(text):
    # 仅生成已有正文的复核关联；绝不据此声称精确覆盖或自动替换。
    text = re.sub(r"<[^>]*>", "", text)
    return tuple(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", text))


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 原文保持前后空格、占位符和富文本；片段译文只供定向方法拦截参考。
SUGGESTIONS = {
    " (Busy)": "（忙碌）", " (Dead)": "（已死）", " (Shattered)": "（精神崩溃）", " (Upset)": "（心烦意乱）",
    " and ": "和", "and ": "和", " in ": "，在", "Including ": "参与者：",
    " becomes": "变得", " become": "变得", " shatters": "精神崩溃", " shatter": "精神崩溃",
    " dies.": "死亡。", " die.": "死亡。", " and will not recover.": "，且无法恢复。", " upset but will recover overnight.": "心烦意乱，但一夜过后就会恢复。",
    " believes that ": "相信", "believes that ": "相信", "believe that ": "相信", " wants ": "想要", "wants ": "想要", "want ": "想要",
    " gains ": "获得", "gains ": "获得", " loses ": "失去", "loses ": "失去", " no longer ": "不再", " now ": "现在", "to ": "向",
    " will be updated in the <b>Journal</b>.": "会在<b>日志</b>中更新。", ". Their Character Bio": "。其人物资料",
    "Ophelia %s ": "奥菲莉娅%s", "Ophelia learns more about ": "奥菲莉娅进一步了解了",
    "Ophelia learns more about <b>%s</b>. The entry will be updated in the <b>Journal</b>.": "奥菲莉娅进一步了解了<b>%s</b>。相关条目会在<b>日志</b>中更新。",
    '<b>Ophelia</b> acquires the information "%s."': '<b>奥菲莉娅</b>获得了信息“%s”。',
    '<b>Outcome:</b>\n': '<b>结果：</b>\n', "Back Down": "退让", "Stay": "留下", "Let It Burn": "任它烧毁",
    "Build: {0} made on {1}": "构建版本：{0}，构建日期：{1}", "Epilogue": "尾声", "Wednesday": "星期三",
    "Faster": "较快", "Fastest": "最快", "Instant": "立即显示", "Quit": "退出", "Okay": "确定",
    "Go to {0}?": "前往{0}？", "Rosie": "罗茜", "Guilda": "吉尔妲", "Object": "物品", "Try Again": "再试一次", "Continue?": "继续？",
    "Enter ": "入场：", "Exit ": "退场：", "Exeunt ": "退场：", "Sacrifice %s for %s": "牺牲%s，换取%s",
    "Ophelia's current event is interrupted by a sudden interlude.": "奥菲莉娅当前参与的事件被突如其来的插曲打断了。",
    "Development Team": "开发团队", "Voice Actors": "配音演员", "Special Thanks": "特别鸣谢", "Kickstarter Backers": "Kickstarter 支持者", "Elsinore Pets": "《Elsinore》的宠物们",
    "\n\nThanks for playing!": "\n\n感谢游玩！", "Ver. %s%s%s [%s]": "版本 %s%s%s [%s]", " (dev)": "（开发版）",
}
SUGGESTIONS.update({
    '\n\n\n\n\nA Game by Golden Glitch Studios\n\n\n\n\n\n\n\n\n\n\n': '\n\n\n\n\nGolden Glitch Studios 出品\n\n\n\n\n\n\n\n\n\n\n',
    '\n\n\n\n\n\n<size=800%%><sprite="Credits-Sprites" name="Wwise-Logo"><size=100%%>\n\n\nPowered by Wwise © 2006 – 2020 Audiokinetic Inc. All rights reserved.\n': '\n\n\n\n\n\n<size=800%%><sprite="Credits-Sprites" name="Wwise-Logo"><size=100%%>\n\n\n采用 Wwise 技术 © 2006 – 2020 Audiokinetic Inc. 保留所有权利。\n',
    'Button icons by Nicolae Berbece, licensed under CC0.\n': '按钮图标由 Nicolae Berbece 制作，采用 CC0 许可。\n',
    'Uses Rewired © 2014 – 2020 Guavaman Enterprises. All rights reserved.\n': '使用 Rewired © 2014 – 2020 Guavaman Enterprises. 保留所有权利。\n',
    'Uses Steamworks.NET © 2013 – 2020 Riley Labrecque, licensed under MIT license.\n': '使用 Steamworks.NET © 2013 – 2020 Riley Labrecque，采用 MIT 许可。\n',
    'ERROR': '错误',
    'ERROR: UNFORMATTED: %s': '错误：未格式化：%s',
    'NONAME': '未命名',
    'NO CHARACTER BIO': '暂无人物资料',
})
for singular in (True, False):
    noun = "a future event" if singular else "future events"
    pronoun = "it" if singular else "they"
    condition = "it can" if singular else "these can"
    tail = f" If {condition} happen in this world, {pronoun} will appear on the <b>Timeline</b>."
    zh = "一个未来事件" if singular else "一些未来事件"
    for details in (False, True):
        source = f"<b>Ophelia</b> learns about {noun}" + (" in which %s" if details else ".") + tail
        target = f"<b>奥菲莉娅</b>得知了{zh}" + ("：%s" if details else "。") + "如果能在当前世界发生，就会显示在<b>时间线</b>上。"
        SUGGESTIONS[source] = target
for noun, zh in (("an event", "一个事件"), ("multiple events", "多个事件")):
    SUGGESTIONS[f"<b>Ophelia</b> learns about {noun}."] = f"<b>奥菲莉娅</b>得知了{zh}。"
    SUGGESTIONS[f"<b>Ophelia</b> learns about {noun} in which %s"] = f"<b>奥菲莉娅</b>得知了{zh}：%s"


def classify(source, item):
    owner = item["owner"]
    context = "\n".join(item["context"])
    # 严格定位真正的 ldstr 之后，避免把相邻另一个字串的消费当作本字串证据。
    anchor = next(i for i, line in enumerate(item["context"]) if line.startswith(item["il_offset"] + ":"))
    after = "\n".join(item["context"][anchor + 1:])
    next_load = next((i for i, line in enumerate(item["context"][anchor + 1:]) if ": ldstr " in line), len(item["context"]))
    direct_after = "\n".join(item["context"][anchor + 1:][:next_load])
    stripped = re.sub(r"<[^>]*>", "", source)
    stripped = re.sub(r"\{[^}]*\}|%[-+\d.]*[A-Za-z%]", "", stripped)
    if not ENGLISH.search(stripped):
        return "exclude", "format_only", "仅富文本、格式占位符或无英文字母，不含待译语言"
    if "Rewired.Demos." in owner:
        return "exclude", "third_party_demo", "Rewired 示例/演示控制器界面，非游戏正式 UI；按实际 owner 排除"
    if "Elsinore.Ui.ElsinoreConsole" in owner or "Elsinore.Ui.DebugUI" in owner or "Agakme.Console." in owner or "Elsinore.Game.Analysis" in owner:
        return "exclude", "developer_debug_ui", "开发控制台、分析输出或调试 FPS；不纳入玩家汉化词表"
    if "GameDataGenerated" in owner or "TutorialDataGenerated" in owner or "PerfectDayDataGenerated" in owner:
        if source == "Continue?" and "EndingGameOver" in after:
            return "translate", "ending_button", "编译结局把字串传给 EndingGameOver 作为玩家按钮文案，非剧情对白"
        if "addDialogue(" in direct_after and "stelem.ref" in direct_after:
            return "exclude", "dialogue_control_tag", "字串写入 addDialogue 第三参数控制标签数组（如 drawblade）；并非对白正文"
        if "::Invoke_" in owner and "Dialogue" in direct_after:
            return "uncertain", "dialogue_existing_mapping", "编译剧情对白消费：本轮不重译；需比对已有正文的富文本/标点映射（包括单词对白）"
        if re.fullmatch(r"[A-Za-z0-9_.$]+", source) and source not in SUGGESTIONS:
            return "exclude", "generated_identifier", "生成剧情的场景/人物/音效/情绪或控制标识；不是展示原句；保留实际 IL 引用"
        if "::Invoke_" in owner and ("Dialogue" in after or re.search(r"[ \u2014?!<>]", source)):
            return "uncertain", "dialogue_existing_mapping", "编译剧情正文差异：本轮不重译；需比对已有正文的富文本/标点映射"
        return "exclude", "generated_identifier", "生成剧情的数据、跳转标签或控制参数；非本轮补译 UI"
    if "System.Void UnityEngine.Debug::Log" in after or "Elsinore.Logging" in after or "Elsinore.Log." in after:
        return "exclude", "runtime_log", "此 ldstr 消费到日志/遥测，不是屏幕文案"
    if "newobj System.Void System." in after and re.search(r"(?:Exception|ArgumentException|InvalidOperationException)", after):
        return "exclude", "exception_message", "内部异常诊断文案，不是正常玩家流程 UI"
    if source in SUGGESTIONS:
        if "::Parse(" in owner or "::ToJson(" in owner or "::From" in owner:
            return "exclude", "serialization_key", "同字串在此方法用作序列化字段/标记，必须保留英文"
        if source == "Instant" and "Elsinore.Ui.DialogueUI" not in owner:
            return "exclude", "internal_identifier", "同字串此处为内部参数，不属于显示选项"
        if source in {'ERROR', 'ERROR: UNFORMATTED: %s', 'NONAME', 'NO CHARACTER BIO'}:
            return "translate", "player_visible_fallback", "已逐IL确认缺资料/姓名/格式错误的兜底写入玩家用StringBuilder或TMP字段，纳入可见文案；不改错误逻辑"
        return "translate", "player_ui", "玩家可见按钮、提示、人物状态或运行时语言片段；依据真实方法消费纳入"
    if source == "Should I do this thing? This is a pretty long string.":
        return "exclude", "overwritten_ui_test_placeholder", "ConfirmationDialog.Awake的测试占位；Activate在显示前以Item2真实提示覆盖text字段，见assembly-placeholder-paths.il.txt"
    if source == "test\ntest\ntest":
        return "exclude", "unused_ui_test_dialog", "GameOverUI.Awake遗留测试弹窗；mundaneGameOverMessage/Dialog仅Awake写入而无读取，正式Activate先DisableAllChildren并选择真实页面，见assembly-placeholder-paths.il.txt"
    if source in {"ElsinoreUiSelectable {0} didn't receive an OnPointerUp event after {1} frames!!", "Ending {0} not configured in credits!", "Failed to get first line TEMP", 'Posting new music event "{0}" from the CreditsPlayer.', "Using {0} for initial UI input mode.", "FadeInfo({0},{1})"}:
        return "exclude", "ui_technical_diagnostic", "已逐条复核：输入事件、鸣谢音频、UI初始化日志或FadeInfo技术表示，无玩家显示消费"
    if source == "Day %s, %s:%s" and "GTime::toHumanString" in owner:
        return "exclude", "unused_legacy_formatter", "两份程序集均没有对此遗留GTime格式方法的调用者；当前UI走GameClock/UiStrings路径"
    if "Elsinore.Game.Credits" in owner:
        if re.fullmatch(r"[a-zA-Z0-9_./-]+", source):
            return "exclude", "credits_data_key", "鸣谢数据字段/技术资源名；品牌和人名保持原样"
        return "translate", "credits_display", "鸣谢页可见句子/标签；保留人名、品牌、许可名称及富文本"
    if "Elsinore.Game.Model::format" in owner or "Elsinore.Game.Model::posstr@" in owner:
        if source in {"ERROR", "NONAME"} or source.startswith("ERROR:"):
            return "uncertain", "ui_error_fallback", "显示格式器兜底错误，可能上屏；不能当正常语言加入词表"
        if re.fullmatch(r"[A-Za-z_]+", source) and not source.endswith(" "):
            return "exclude", "logic_identifier", "模型格式器中的逻辑谓词或数据键；需按调用用途保留英文"
        return "uncertain", "ui_formatter_fragment", "UI 语言格式器中的未覆盖片段，需要定向确认语序/类型后翻译"
    if re.search(r"Elsinore\.Ui\.", owner):
        if source in {"NO CHARACTER BIO", "Should I do this thing? This is a pretty long string.", "test\ntest\ntest"}:
            return "uncertain", "ui_placeholder", "UI 初始化测试/缺数据兜底；是否实际可见尚需确认"
        if re.search(r"GetField|GetFields|Find\(|GetComponent|Animator::|SetTrigger|Load|String::(?:op_Equality|Equals)|TimelineIconMap|::get_Category|Logging", after):
            return "exclude", "ui_internal_identifier", "UI 方法中的对象名、资源路径、动画/比较键或遥测标签，不是显示语言"
        if re.fullmatch(r"[A-Za-z0-9_./:{}-]+", source):
            return "exclude", "ui_internal_identifier", "UI 内部对象、字段、资源/音效/动作标识；未用于可见语言输出"
        return "uncertain", "ui_use_unknown", "UI 所属但缺少明确展示消费证据；需保留核查，不能直接翻译"
    if owner.endswith("::ToString()") or "::DebugString(" in owner:
        return "exclude", "technical_repr", "对象的技术诊断表示；模板保留类型/字段格式，未作为玩家语言"
    if "Elsinore.Script::extractReferencedCharacters" in owner:
        return "exclude", "english_alias_lookup", "英文称谓用于脚本人物引用提取/比较，翻译会破坏原文匹配"
    if re.search(r"Elsinore.Game.(?:Scheduler|HighLevelScheduler|Timeline|NameList|PetList|Schedule|InformationList|EndingList|CloseupList|AnimationList|CharAnimList|ElsinoreDataEx)|Agakme.(?:Logic|Pathfinding)|Elsinore.Game.Model::(?:logicDomain|calculateStaticScheduleData|makeBasicAtom)|GameRunner::(?:CompileContent|StateFromProgress)|GameRunner/StateFromProgress", owner):
        return "exclude", "logic_or_scheduler_diagnostic", "逻辑/调度/资料查找方法中的内部断言、进度标签或技术诊断；非玩家历史格式器"
    if re.search(r"Elsinore\.(?:.+Direction|MovementSkipHandler|MovementSaveLoader)|CharacterBehavior|IsometricCamera|RoomMarker|PetBehavior|SaveLoad|ObjectTracker|VisibilityManager|StageDirectionManager|LoadingScreen|ImTheBoss::updateTick|ScheduleManager::(?:updateScene|triggerNewAction)|GraphicsPreferenceManager", owner):
        return "exclude", "engine_diagnostic", "移动、音频、保存或场景执行的错误/性能记录，按方法职责排除；本轮明确可见的提示已单独纳入"
    if source in {"%s$section%s", "%s_%s.png", "%sx%s", "%sx%s@%s", "e:%s:%s:%s", "i:%s", "p:%s:%s"}:
        return "exclude", "technical_template", "场景键、资源文件名、分辨率数字或内部事件缓存键模板，没有待译语言"
    if re.search(r"::(?:Parse|ToJson|FromJson|Serialize|Deserialize|Load|ApplySerialized|Generate)|Json|CodeGenerator|Scripting|Validation|Papika|Ak[A-Z]|AK\.|Rewired\.|SteamManager|Logging|SoundManager|CharacterMovement|MoveUtils|PlayerMove|HSBColor|HSBColor|HSBColor|MirrorReflection", owner):
        return "exclude", "technical_non_ui", "实际 owner 属于解析/序列化/编译/校验/引擎/音频/移动/遥测；其语言为技术诊断或标识"
    if re.fullmatch(r"[A-Za-z0-9_.$/<>:{}=-]+", source):
        return "exclude", "internal_identifier", "内部字段、方法、资源、类型、枚举或逻辑标识；保留实际 owner 供复核"
    return "uncertain", "non_ui_use_unknown", "未明确证明为玩家文案或技术诊断；另列待确认，避免凭长度/标点排除"


def unwrap_italic(text):
    """只去除包裹整句的完整外层斜体；保留句中强调标签。"""
    count = 0
    while text.startswith("<i>") and text.endswith("</i>"):
        depth = 0
        closed_at = None
        for match in re.finditer(r"</?i>", text):
            depth += -1 if match.group() == "</i>" else 1
            if depth == 0:
                closed_at = match.end()
                break
        if closed_at != len(text):
            break
        text = text[3:-4]
        count += 1
    return text, count


def strict_alias_key(text):
    text, wrappers = unwrap_italic(text)
    # 编译器把双连字符及其邻接空格格式化成无空格长破折号。
    text = re.sub(r"\s*—\s*", "—", text.replace("--", "—"))
    return normalize(text), wrappers


def make_existing_alias(record, candidates, translations_path):
    key, wrappers = strict_alias_key(record["source"])
    eligible = [x for x in candidates if strict_alias_key(x["source"])[0] == key]
    if not eligible:
        record["mapping_note"] = "严格核对外层斜体与编译器破折号转换后仍无相同原文；保留待确认，不能仅凭词序相同复用"
        return None
    nearest = min(abs(wrappers - strict_alias_key(x["source"])[1]) for x in eligible)
    eligible = [x for x in eligible if abs(wrappers - strict_alias_key(x["source"])[1]) == nearest]
    if len({x["target"] for x in eligible}) != 1:
        record["mapping_note"] = "严格相同原文出现不同已有译文；保留待确认，不自动选择意义或语气"
        return None
    existing = sorted(eligible, key=lambda x: x["id"])[0]
    existing_wrappers = strict_alias_key(existing["source"])[1]
    delta = wrappers - existing_wrappers
    target = existing["target"]
    if delta < 0:
        record["mapping_note"] = "已有译文包含比实际原文更多的整句斜体；需单独复核去标签，暂不自动处理"
        return None
    target = "<i>" * delta + target + "</i>" * delta
    alias = {
        "id": "asm-alias-" + record["source_sha256"][:16],
        "source": record["source"],
        "text": record["source"],
        "source_sha256": record["source_sha256"],
        "target": target,
        "target_sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
        "existing_id": existing["id"],
        "existing_source": existing["source"],
        "existing_target": existing["target"],
        "existing_source_sha256": hashlib.sha256(existing["source"].encode("utf-8")).hexdigest(),
        "existing_target_sha256": hashlib.sha256(existing["target"].encode("utf-8")).hexdigest(),
        "adjustments": {"outer_italic_wrappers_added": delta, "target_punctuation_changed": False, "target_meaning_changed": False},
        "review_reason": "已逐条核对英文内容、内部富文本和所有其他标点；差异仅整句外层斜体、--到—与其邻接空格；中文意义和标点原样复用",
        "provenance": {"kind": "frozen_existing_translation_format_alias", "translations_path": str(translations_path.relative_to(ROOT)).replace("\\", "/"), "translations_sha256": hashlib.sha256(translations_path.read_bytes()).hexdigest(), "existing_batch": existing["batch"], "audit_source": "assembly-strings.json", "usages": [{"assembly": u["assembly"], "owner": u["owner"], "il_offsets": u["il_offsets"]} for u in record["usages"]]},
    }
    record["decision"] = "reuse_existing"
    record["alias_id"] = alias["id"]
    record["alias_of"] = existing["id"]
    record["mapping_note"] = alias["review_reason"]
    record["suggested_target"] = target
    for usage in record["usages"]:
        if usage["decision"] == "uncertain":
            usage.update(decision="reuse_existing", category="existing_format_alias", reason=alias["review_reason"])
    return alias


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    raw_path = OUT / "assembly-raw-occurrences.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8-sig"))
    translations_path = ROOT / "translation/sol-full-2026-10-09/translations.json"
    translations = json.loads(translations_path.read_text(encoding="utf-8-sig"))
    covered = collections.defaultdict(list)
    dialogue_lookup = collections.defaultdict(list)
    for row in translations:
        covered[normalize(row["source"])].append(row["id"])
        dialogue_lookup[dialogue_match_key(row["source"])].append(row)
    groups = collections.defaultdict(list)
    for item in raw:
        groups[item["source"]].append(item)
    records = []
    aliases = []
    translations_by_id = {x["id"]: x for x in translations}
    for source, occurrences in sorted(groups.items()):
        ids = covered.get(normalize(source), [])
        usages = []
        for item in occurrences:
            decision, category, reason = classify(source, item)
            usage = {k: item[k] for k in ("assembly", "owner", "il_offset")}
            usage.update(decision=decision, category=category, reason=reason)
            if decision in {"translate", "uncertain"} and not ids:
                usage["context"] = item["context"]
            usages.append(usage)
        decisions = {x["decision"] for x in usages}
        decision = "covered" if ids else "translate" if "translate" in decisions else "uncertain" if "uncertain" in decisions else "exclude"
        # 同一方法内重复 ldstr 合并偏移数组；不丢失任何真实方法/偏移。
        grouped_usages = {}
        for usage in usages:
            key = tuple(usage[k] for k in ("assembly", "owner", "decision", "category", "reason"))
            if key not in grouped_usages:
                grouped_usages[key] = {k: usage[k] for k in ("assembly", "owner", "decision", "category", "reason")}
                grouped_usages[key]["il_offsets"] = []
                if "context" in usage:
                    grouped_usages[key]["contexts"] = []
            grouped_usages[key]["il_offsets"].append(usage["il_offset"])
            if "context" in usage:
                grouped_usages[key]["contexts"].append({"il_offset": usage["il_offset"], "instructions": usage["context"]})
        record = {"id": "asm-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:16], "source": source, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(), "normalized": normalize(source), "contains_english": bool(ENGLISH.search(source)), "covered_by": ids, "decision": decision, "occurrence_count": len(usages), "usages": list(grouped_usages.values())}
        if decision == "uncertain" and any(u["category"] == "dialogue_existing_mapping" for u in usages):
            record["existing_translation_candidates"] = [{"id": x["id"], "source": x["source"], "target": x["target"]} for x in dialogue_lookup.get(dialogue_match_key(source), [])]
            record["mapping_note"] = "按删除富文本后的英文字词序列关联；仅供复核，标点、语气或富文本差异不能直接当精确覆盖"
            alias = make_existing_alias(record, [translations_by_id[x["id"]] for x in record["existing_translation_candidates"]], translations_path)
            if alias:
                aliases.append(alias)
        if decision == "translate":
            record["suggested_target"] = SUGGESTIONS.get(source)
            record["implementation_note"] = "片段/模板优先定向拦截格式器或完整输出；不得全局替换内部标识，不把 ldstr 模板词表覆盖误说成拼接整句已覆盖"
        records.append(record)
    save("assembly-strings.json", records)
    save("assembly-existing-aliases.json", aliases)
    for decision, name in (("translate", "assembly-ui-candidates.json"), ("exclude", "assembly-exclusions.json"), ("uncertain", "assembly-uncertain.json")):
        save(name, [x for x in records if x["decision"] == decision and x["contains_english"]])
    summary = {"source_assemblies": [{"path": str(Path(r"D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data\Managed") / name), "sha256": hashlib.sha256((Path(r"D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data\Managed") / name).read_bytes()).hexdigest()} for name in ("Assembly-CSharp.dll", "Elsinore.dll")], "translations_sha256": hashlib.sha256(translations_path.read_bytes()).hexdigest(), "normalization": "仅折叠空白并 trim，保留大小写、富文本、标点；不设词数/长度门槛", "ldstr_occurrences": len(raw), "unique_strings": len(records), "unique_english_strings": sum(x["contains_english"] for x in records), "decisions": dict(collections.Counter(x["decision"] for x in records)), "english_decisions": dict(collections.Counter(x["decision"] for x in records if x["contains_english"])), "excluded_categories": dict(collections.Counter(u["category"] for x in records if x["decision"] == "exclude" and x["contains_english"] for u in x["usages"])), "scope": "静态覆盖审核，不启动游戏、不接触存档、不重译正文、不调用网络或付费模型", "dynamic_display_paths": [{"owner": "Elsinore.Ui.UiStrings::FormatRoomId", "source_field": "RoomMarker.playerFacingName", "note": "地图/时间线房间显示名来自场景字段，names.locations 是内部ID"}, {"owner": "ObservableSceneObject::Elsinore.Ui.IInteractable.get_Tooltip", "source_field": "ObservableSceneObject.ObjectName", "note": "物品tooltip直接读取场景字段，names.observables不能当显示名翻译"}], "evidence": "assembly-ui-paths.il.txt", "review_limits": "未确定可见的字符串保留 uncertain；covered 表示现有规范化源词表命中，不等于动态拼接整句或像素显示验证通过"}
    summary["uncertain_categories"] = dict(collections.Counter(u["category"] for x in records if x["decision"] == "uncertain" for u in x["usages"]))
    summary["dialogue_existing_candidate_matches"] = sum(bool(x.get("existing_translation_candidates")) for x in records if x["decision"] == "uncertain")
    summary["existing_format_aliases"] = len(aliases)
    summary["existing_format_alias_file"] = "assembly-existing-aliases.json"
    summary["placeholder_review_evidence"] = "assembly-placeholder-paths.il.txt"
    summary["existing_format_alias_policy"] = "只复用冻结译文；中文意义和标点不改，只按真实原文补整句外层斜体；不会覆盖冻结raw或原translations.json"
    save("assembly-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
