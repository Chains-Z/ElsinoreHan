"""从完整房间字段审计及冻结姓名制备地图确认框规则，不改既有词表或导出文件。"""

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "analysis/ui-audit"
FULL = ROOT / "translation/sol-full-2026-10-09"
OUT = ROOT / "translation/supplemental"
EVIDENCE = AUDIT / "map-confirmation-source-evidence.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build():
    """完整白名单来自所有已审字段，包含先前已翻译而未进入补译候选的房间。"""
    audit = read(AUDIT / "resource-strings.json")
    translations = {row["source"]: row for row in read(FULL / "translations.json")}
    template = translations["Go to {0}?"]
    room_rows = [row for row in audit if row.get("origin", {}).get("class") == "RoomMarker"
                 and row["origin"].get("field") == "playerFacingName"]
    character_rows = [row for row in audit if row.get("origin", {}).get("asset") == "name_mapping"]
    groups = {"room": room_rows, "character": character_rows}
    records = []
    for kind, rows in groups.items():
        for source in sorted({row["source"] for row in rows}):
            leaf = translations.get(source)
            if leaf is None and source != "???":
                raise ValueError("地图参数缺少冻结译文：" + source)
            records.append({"kind": kind, "source": source, "source_sha256": digest(source),
                            "target": leaf["target"] if leaf else source,
                            "translation_id": leaf["id"] if leaf else None,
                            "origins": [row["origin"] for row in rows if row["source"] == source]})
    destinations = sorted({row["source"] for row in records}, key=lambda value: (-len(value), value))
    rule = {"id": "ui-rule-map-go-to-destination", "priority": 30,
            "pattern": "^Go to (?<destination>(?:" + "|".join(map(re.escape, destinations)) + r"))\?\z$",
            "replacement": template["target"].replace("{0}", "${destination}"),
            "origins": ["analysis/ui-audit/map-confirmation-source-evidence.json",
                        "Assembly-CSharp.dll:MapUI/<>c__DisplayClass32_0::<Awake>b__2 IL_003e..0070",
                        "Assembly-CSharp.dll:MapUI::<IInitializable.Initialize>b__33_0 IL_002a..0047",
                        "analysis/ui-audit/resource-strings.json:RoomMarker.playerFacingName/name_mapping"],
            "note": "仅地图真实Go to {0}?模板及完整已审房间/人物显示值；复用冻结叶子，不翻内部ID、不放宽通用短模板门槛；严格末尾锚点，逆序首匹配失败不另找规则兜底"}
    tests = []
    for record in records:
        source = template["source"].replace("{0}", record["source"])
        target = template["target"].replace("{0}", record["target"])
        tests.append({"id": "map-" + record["kind"] + "-" + digest(record["source"])[:12],
                      "source": source, "target": target,
                      "source_sha256": digest(source), "target_sha256": digest(target),
                      "parameter_source": record["source"], "parameter_kind": record["kind"],
                      "origins": ["analysis/ui-audit/map-confirmation-source-evidence.json",
                                  "translation/sol-full-2026-10-09/translations.json:" + template["id"]],
                      "verification_level": "component",
                      "note": "真实模板与真实显示字段的格式组件回填；不声称这些目的地在当前存档都可导航或已实际确认移动"})
    negatives = ["Go to upper_hallway?", "Go to internal_room?", "Go to hamlet?", "Go to Unknown Room?",
                 "Go to Upper Hallway East?", "Go to Upper Hallway •?", "Go to Upper Hallway??",
                 "Go to Upper Hallway? extra", "Go to <b>Upper Hallway</b>?", "go to Upper Hallway?",
                 "Go to Upper\nHallway?", "Go to Upper Hallway?\nMore information", "Go to 42?", "Go to 已译房间?"]
    for index, source in enumerate(negatives):
        tests.append({"id": "map-reject-" + str(index + 1), "source": source, "target": None,
                      "source_sha256": digest(source),
                      "origins": ["analysis/ui-audit/map-confirmation-source-evidence.json"],
                      "verification_level": "component",
                      "note": "明确构造的内部ID、未知参数或额外结构负例；非真实游戏正文，应拒绝完整消费"})
    return [rule], tests, records, template, groups


def main():
    rules, tests, records, template, groups = build()
    evidence = read(EVIDENCE)
    evidence.update({"scope": "截图地图确认框漏译的静态源及真实XUnity格式组件核查；不启动游戏或确认移动",
                     "template": template,
                     "template_literal_length_without_parameter": len(template["source"].replace("{0}", "")),
                     "root_cause": "Go to {0}?已有冻结译文，但通用format_rule因去掉参数后长度7小于10未导出；房间名独立已有译文",
                     "room_occurrences": len(groups["room"]),
                     "room_unique_display_names": len({row["source"] for row in groups["room"]}),
                     "character_occurrences": len(groups["character"]),
                     "character_unique_display_names": len({row["source"] for row in groups["character"]}),
                     "destinations": records,
                     "component_cases": len(tests), "positive_cases": len(records), "negative_cases": len(tests) - len(records),
                     "rule_ids": [rule["id"] for rule in rules],
                     "limitations": ["完整RoomMarker字段与姓名映射是实际显示参数的静态上界，不宣称全部都在地图可达",
                                     "未知人物标记???原样保留；不从内部人物ID反推显示名",
                                     "组件消费通过不代表已通过真实地图按钮集成或物理输入E2E"]})
    evidence["source_artifact_sha256"] = {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (AUDIT / "resource-strings.json", FULL / "character-names.json")}
    save(OUT / "map-ui-rules.json", rules)
    save(OUT / "map-ui-tests.json", tests)
    save(EVIDENCE, evidence)
    print(json.dumps({"rules": len(rules), "rooms": evidence["room_unique_display_names"],
                      "characters": evidence["character_unique_display_names"], "tests": len(tests)}))


if __name__ == "__main__":
    main()
