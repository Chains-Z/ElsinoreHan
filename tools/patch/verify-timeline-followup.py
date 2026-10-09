"""核对时间线真实按钮证据与资源格式器重放；二者分别报告。"""
from __future__ import annotations

import argparse
import base64
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TAIL = "\n<line-height=40%>\n<line-height=90%>"
REPLAY_KEYS = {
    "replay-hamlet-sleep": "timeline-followup-full-empty-hamlet-sleep",
    "replay-polonius-question": "timeline-followup-full-empty-polonius-question",
    "replay-horatio-queen": "timeline-followup-full-empty-horatio-queen",
    "replay-hamlet-play": "timeline-followup-full-empty-hamlet-play",
    "replay-queen-not-attended": "timeline-followup-queen-not-attended-detail",
}


def unbase(value: str) -> str:
    """严格恢复UTF-8正文，拒绝截断或非法编码。"""
    return base64.b64decode(value, validate=True).decode("utf-8")


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def truth(value):
    require(value in {"True", "False"}, "证据布尔值不完整")
    return value == "True"


def load_contracts():
    translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
    tests = json.loads((ROOT / "translation/supplemental/timeline-followup-tests.json").read_text(encoding="utf-8"))
    resources = json.loads((ROOT / "analysis/ui-audit/resource-ui-candidates.json").read_text(encoding="utf-8"))
    targets = {row["source"]: row["target"] for row in translations}
    frozen_tests = {row["id"]: row for row in tests}
    event_ids = {row["source"]: {origin["record_id"] for origin in row["origins"]
                 if origin.get("asset") == "schedule"} for row in resources if "origins" in row}
    return targets, frozen_tests, event_ids


def english_list(names):
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + ", and " + names[-1]


def chinese_list(names, targets):
    translated = [targets[name] for name in names]
    return translated[0] if len(names) == 1 else "、".join(translated[:-1]) + "和" + translated[-1]


def empty_expected(row, targets):
    """以冻结正文和真实有限名单为oracle，完整核对原格式器空尾段。"""
    source, secondary = unbase(row[12]), unbase(row[14])
    room, description = unbase(row[8]), unbase(row[9])
    names = unbase(row[10]).splitlines()
    require(names and len(names) == int(row[6]) and len(unbase(row[11]).splitlines()) == len(names), "真实参与者名单来源数量不符")
    expected_secondary = "<line-height=90%>Including " + english_list(names) + "." + TAIL
    require(secondary == expected_secondary and source.endswith(secondary), "真实空尾段/完整名单源不符")
    require(truth(row[15]), "真实无Changes事件缺少待复现的空尾段")
    primary = source[:-len(TAIL + secondary)]
    require(source == primary + TAIL + secondary, "时间线两个真实builder合并不完整")
    pattern = r"^<line-height=90%>(Wednesday|Thursday|Friday|Saturday|Sunday), ([0-9]{2}:[0-9]{2}) in (.*), <i>in which</i> ([\s\S]+)$"
    match = re.fullmatch(pattern, primary)
    require(match is not None, "真实事件标题格式超出已审契约")
    day, clock, actual_room, actual_description = match.groups()
    require(actual_room == room and actual_description == description, "详情来源与实际源正文不一致")
    return ("<line-height=90%>" + targets[day] + " " + clock + "，" + targets[room]
            + "，<i>事件：</i>" + targets[description] + TAIL + "<line-height=90%>参与者："
            + chinese_list(names, targets) + "。" + TAIL)


def verify_rows(rows, *, require_real=True):
    """只有明确的真实按钮记录提高剧情覆盖，重放无法代替真实记录。"""
    targets, tests, event_ids = load_contracts()
    by_tag = defaultdict(list)
    for row in rows:
        require(row and row[0], "证据存在空行或无类型记录")
        by_tag[row[0]].append(row)
    require(by_tag["SCHEMA"] == [["SCHEMA", "1"]], "时间线探针schema缺失或重复")
    require(len(by_tag["STATUS"]) == 1 and by_tag["STATUS"][0][1] == "COMPLETE", "时间线探针未完成")
    require(not by_tag["FAILURE"], "时间线探针存在失败记录")
    require(len(by_tag["START_LOOP"]) == 1, "缺少起始循环来源")
    require(len(by_tag["INITIAL_DETAIL"]) == 1, "缺少最初真实详情的恢复来源")
    initial = by_tag["INITIAL_DETAIL"][0]
    require(len(initial) == 5 and unbase(initial[1]) and sha(unbase(initial[2])) == initial[3] and truth(initial[4]), "最初真实详情源或归属不完整")
    status = by_tag["STATUS"][0]
    require(len(status) == 4 and float(status[3]) <= 12.5, "时间线额外采集时间超出约10秒预算")
    current_loop = int(by_tag["START_LOOP"][0][1])
    visited = {current_loop}
    for row in by_tag["LOOP_NAV"]:
        require(len(row) == 5 and row[1] in {"PreviousLoopButton.OnClick", "NextLoopButton.OnClick"}, "历史循环未通过真实左右按钮导航")
        before, after = int(row[2]), int(row[3])
        delta = 1 if row[1].startswith("Previous") else -1
        require(before == current_loop and after == before + delta and truth(row[4]), "历史循环按钮请求未完成")
        current_loop = after
        visited.add(after)
    require(current_loop == int(by_tag["START_LOOP"][0][1]), "真实左右按钮未恢复最初loop")
    require(len(by_tag["RESTORE"]) == 1, "缺少最初真实详情恢复证据")
    restore = by_tag["RESTORE"][0]
    require(len(restore) == 8 and restore[7] == "original-item.button.OnClick", "最初详情恢复未通过真实原按钮")
    require(int(restore[1]) == current_loop and restore[2] == initial[1] and restore[3] == initial[2]
            and restore[4] == initial[2] and truth(restore[5]) and truth(restore[6]), "原loop/详情正文或UI归属没有恢复")
    records = {}
    expectations = {}
    real_empty = 0
    for row in by_tag["REAL"]:
        require(len(row) == 20 and ("REAL", row[1]) not in records, "真实时间线证据结构或唯一性不符")
        require(row[17:19] == ["button.OnClick", "currentItems"], "真实详情未绑定合法按钮和Details来源")
        if truth(row[5]):
            require(row[19] == "TimelineItem.Details(lastUsedGameState)" and int(row[7]) >= 0, "已参加事件未绑定真实Details来源")
        else:
            require(row[19] == "Details-not-called" and int(row[7]) == -1, "未参加事件不得调用Details或虚构零Changes")
        require(int(row[2]) in visited and unbase(row[3]), "真实事件循环/键来源缺失")
        source, description, room = unbase(row[12]), unbase(row[9]), unbase(row[8])
        require(source and sha(source) == row[13] and truth(row[16]), "真实源完整性或当前UI归属失败")
        require(description in targets and row[4] in event_ids.get(description, set()), "真实事件正文未绑定冻结资源来源")
        if truth(row[5]) and int(row[7]) == 0 and int(row[6]) > 0:
            expectations[("REAL", row[1])] = empty_expected(row, targets)
            real_empty += 1
        else:
            require(room == "Gertrude's Chambers", "真实代表性事件不属于待验证的分支")
        records[("REAL", row[1])] = (source, row)
    require(int(status[2]) == len(by_tag["REAL"]), "真实详情数量汇总不符")
    skips = []
    for row in by_tag["SKIP"]:
        require(len(row) == 12 and int(row[1]) in visited and unbase(row[2]) and row[3]
                and sha(unbase(row[6])) == row[7], "跳过项缺少真实循环/事件/源哈希")
        attended, future = truth(row[4]), truth(row[5])
        if row[8] == "not-attended-or-future":
            require((not attended or future) and row[10] == "Details-not-called" and not unbase(row[9]), "未参加/未来项不应提前调用Details")
        elif row[8] == "details-missing-scene":
            require(attended and not future and row[10] in {"TimelineItem.Details(lastUsedGameState)", "createEventContent->TimelineItem.Details(lastUsedGameState)"}
                    and "KeyNotFoundException" in unbase(row[9]) and unbase(row[11]), "缺场景Changes记录未保留真实异常来源")
        else:
            raise ValueError("跳过项原因超出已审异常分支")
        skips.append({"event_id": row[3], "reason": row[8], "scene_ids": unbase(row[11]).splitlines()})
    require(not require_real or real_empty > 0, "真实冻结存档没有验证到已参加且无Changes的参与者空尾段事件；组件重放不能代替")
    require({row[1] for row in by_tag["REPLAY"]} == set(REPLAY_KEYS), "截图五种真实资源格式器重放未全部覆盖")
    for row in by_tag["REPLAY"]:
        require(len(row) == 14 and ("REPLAY", row[1]) not in records, "组件重放证据结构或唯一性不符")
        require(row[10:12] == ["real-resource-formatter-component", "not-acquired-story"]
                and row[13] == "ElsinoreEvent.Participants+Observers/UiStrings.FormatCharacterName", "组件重放被错误记为真实剧情或缺失参与者来源")
        description, source = unbase(row[3]), unbase(row[8])
        require(sha(description) == row[4] and sha(source) == row[9], "重放源/事件正文哈希不符")
        require(row[2] in event_ids.get(description, set()), "重放事件ID不是该真实资源正文的来源")
        require(len(unbase(row[7]).splitlines()) == len(unbase(row[12]).splitlines()), "重放参与者显示值与内部ID来源缺失")
        frozen = tests[REPLAY_KEYS[row[1]]]
        require(source == frozen["source"], "真实格式器重放与冻结完整源不符")
        primary = "<line-height=90%>" + unbase(row[6]) + " in " + unbase(row[5]) + ", <i>in which</i> " + description
        require(source.startswith(primary + TAIL), "重放时钟/房间参数不是完整源的真实格式器来源")
        replay_names = unbase(row[7]).splitlines()
        if row[1] != "replay-queen-not-attended":
            require(replay_names and "<line-height=90%>Including " + english_list(replay_names) + "." + TAIL in source,
                    "重放参与者来源与完整名单源不一致")
        else:
            require(not replay_names, "未参加组件重放不应伪造可见参与者")
        records[("REPLAY", row[1])] = (source, row)
        expectations[("REPLAY", row[1])] = frozen["target"]
    states = defaultdict(dict)
    owners = {}
    for row in by_tag["OWNER"]:
        require(len(row) == 14, "当前UI归属详细证据缺失")
        parts = [truth(value) for value in row[4:13]]
        accepted = all(parts[:5]) and (parts[5] or all(parts[6:9]))
        require(accepted and truth(row[13]) == accepted, "当前modal不是Timeline或自己的激活详情弹窗")
        key = tuple(row[1:4])
        require(key not in owners, "当前UI归属证据重复")
        owners[key] = row
    require(("INITIAL", "initial", "translated") in owners, "初始详情归属没有被核对")
    for row in by_tag["STATE"]:
        require(len(row) == 12, "F8三态证据字段缺失")
        key = row[1], row[2]
        require(key in records and row[3] in {"translated", "original", "restored"} and row[3] not in states[key], "F8三态重复或没有源所属记录")
        require((row[1], row[2], row[3]) in owners, "F8正文缺少自己的详情弹窗归属证据")
        source = records[key][0]
        require(unbase(row[5]) == source and row[6] == sha(source) and truth(row[9]), "F8源文完整性或当前UI归属失败")
        require(truth(row[11]) == (row[1] == "REAL"), "真实按钮源与重放源契约混淆")
        if row[1] == "REAL":
            require(unbase(row[8]) == source, "F8期间真实builder源变更")
        states[key][row[3]] = row
    require(set(states) == set(records), "存在没有采集F8的真实详情/组件重放")
    for key, modes in states.items():
        require(set(modes) == {"translated", "original", "restored"}, "正文F8三态未完整采集")
        require(len({row[4] for row in modes.values()}) == 1 and len({row[10] for row in modes.values()}) == 1,
                "F8三态正文控件或真实暂停时钟不一致")
        source = records[key][0]
        translated, original, restored = (unbase(modes[mode][7]) for mode in ("translated", "original", "restored"))
        require(original == source and translated == restored, "F8英文没有恢复完整真实原文或中文无法往返")
        require(not re.search(r"[A-Za-z]", re.sub(r"<[^>]*>", "", translated)), "中文正文仍含英文漏译")
        if key in expectations:
            require(translated == expectations[key], "正文显示与完整冻结译文/格式不同")
        else:
            real = records[key][1]
            require(targets[unbase(real[9])] in translated and targets[unbase(real[8])] in translated, "真实Queen分支的正文/房间译文缺失")
    coverage = {row[1]: row[2] for row in by_tag["COVERAGE"]}
    require(set(coverage) == {"empty-one", "empty-many", "queen-room"}, "代表性真实分支缺少覆盖说明")
    for row in by_tag["COVERAGE"]:
        require(len(row) == 4 and row[2] in {"AVAILABLE", "UNAVAILABLE"} and unbase(row[3]), "真实分支覆盖说明不完整")
        if row[2] == "AVAILABLE":
            available = any((int(real[6]) == 1 if row[1] == "empty-one" else int(real[6]) > 1)
                            and truth(real[5]) and int(real[7]) == 0 for real in by_tag["REAL"])
            if row[1] == "queen-room":
                available = any(unbase(real[8]) == "Gertrude's Chambers" for real in by_tag["REAL"])
            require(available, "真实分支覆盖被组件重放或无关事件冒充")
    require(len(by_tag["STORY_COVERAGE"]) == 5 and len({row[1] for row in by_tag["STORY_COVERAGE"]}) == 5, "截图具体剧情缺少独立未覆盖说明")
    stories = {}
    replay_descriptions = {unbase(row[3]) for row in by_tag["REPLAY"]}
    for row in by_tag["STORY_COVERAGE"]:
        require(len(row) == 4 and row[2] in {"PRESENT_IN_VISITED_ITEMS", "UNAVAILABLE"}
                and unbase(row[1]) in replay_descriptions and row[3], "具体剧情覆盖来源或未覆盖说明不符")
        stories[unbase(row[1])] = row[2]
    return {"passed": True, "real_button_details": len(by_tag["REAL"]), "real_empty_changes_details": real_empty,
            "real_resource_formatter_replays": len(by_tag["REPLAY"]), "coverage": coverage,
            "visited_story_items": stories, "initial_loop_and_detail_restored": True,
            "skipped_items": skips,
            "f8_source_complete": True, "display_matches_frozen_translation": True,
            "limitations": ["资源格式器重放不代表冻结存档已获得该剧情", "未验证物理F8按键或屏幕像素渲染"]}


def verify(path, *, require_real=True):
    rows = [line.split("\t") for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line]
    return verify_rows(rows, require_real=require_real)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path, help="保存机器可读验证摘要")
    parser.add_argument("--allow-no-real-empty-event", action="store_true", help="明确只报告真实分支未覆盖，仍严格核对五种重放")
    args = parser.parse_args()
    proof = verify(args.path, require_real=not args.allow_no_real_empty_event)
    text = json.dumps(proof, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
