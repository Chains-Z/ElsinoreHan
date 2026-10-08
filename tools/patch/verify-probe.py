"""核查真实游戏探针记录，防止菜单词表漏译和中文溢出回归。"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def parse_objects(path: Path) -> list[dict]:
    objects = []
    current = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("OBJECT="):
            current = {"object": line[7:].rsplit(" ACTIVE=", 1)[0], "active": line.endswith("ACTIVE=True")}
            objects.append(current)
        elif current is not None and line.startswith("TEXT="):
            current["text"] = line[5:]
        elif current is not None and line.startswith("OVERFLOW="):
            current["overflow"] = line.split(" ", 1)[0] != "OVERFLOW=False"
    return objects


def evaluate(menu: list[dict], settings: list[dict], menu_text: str, log: str, expected_settings: set | None = None) -> dict[str, bool]:
    """只有目标界面确实出现时，才评估该页的文字溢出。"""
    visible_menu = [item for item in menu if item["active"]]
    visible_settings = [item for item in settings if item["active"]]
    actual = {item.get("text") for item in visible_menu}
    expected = {"设置", "退出游戏"}
    start_labels = {"继续游戏", "开始新游戏"} & actual
    expected |= start_labels
    has_start = bool(start_labels)
    settings_opened = (expected_settings or {"Graphics", "Audio", "Gameplay"}) <= {item.get("text") for item in visible_settings}
    return {
        "menu_labels_all_translated": has_start and expected <= actual,
        "menu_labels_no_overflow": has_start and expected <= actual and all(not item.get("overflow", True) for item in visible_menu if item.get("text") in expected),
        "menu_no_original_labels": not ({"Continue Game", "New Game", "Quit Game", "Options", "Settings"} & actual),
        "chinese_glyphs_available": "GLYPHS_继续游戏设置退出=True" in menu_text,
        "settings_pointer_navigation_logged": "已通过真实设置按钮的 EventSystem 指针事件打开设置界面" in log,
        "settings_page_opened": settings_opened,
        "settings_visible_texts_no_overflow": settings_opened and all(not item.get("overflow", True) for item in visible_settings),
    }


def evaluate_toggle(original: set, restored: set, log: str) -> dict[str, bool]:
    """设置按钮源文可为Options或Settings，必须真的恢复英文并再次显示中文。"""
    return {
        "toggle_original_menu": "Quit Game" in original and bool({"Options", "Settings"} & original)
                                and bool({"Continue Game", "New Game"} & original)
                                and not ({"设置", "退出游戏", "继续游戏", "开始新游戏"} & original),
        "toggle_restored_menu": {"设置", "退出游戏"} <= restored and bool({"继续游戏", "开始新游戏"} & restored),
        "toggle_release_no_change": "F8_RELEASE_NO_CHANGE=True" in log,
    }


def evaluate_settings_options(report: str, translations: dict) -> dict[str, bool]:
    """逐档检查真实槽位，当前显示正确不能替代非当前选项覆盖。"""
    expected = {"text_speed": {"Normal", "Faster", "Fastest", "Instant"},
                "costumes": {"Default", "Modern"}, "quality": {"Low", "Medium", "High"},
                "screen_mode": {"Windowed", "Borderless", "Fullscreen"}, "resolution_native": {"Native"}}
    # 槽位名由真实探针记录，保留别名用于早期字段路径命名。
    aliases = {"TextSpeed": "text_speed", "AlternateCostumes": "costumes", "Quality": "quality", "ScreenMode": "screen_mode", "Resolution": "resolution_native"}
    rows = []
    for line in report.splitlines():
        fields = line.split("\t")
        if fields[0] == "OPTION":
            rows.append({"slot": aliases.get(fields[1], fields[1]), "source": base64.b64decode(fields[3]).decode("utf-8"),
                         "target": base64.b64decode(fields[4]).decode("utf-8"), "mode": fields[5], "overflow": fields[6] == "True", "active": fields[7] == "True"})
    translated = [r for r in rows if r["mode"] == "translated"]
    original = [r for r in rows if r["mode"] == "original"]
    restored = [r for r in rows if r["mode"] == "restored"]
    return {"settings_all_noncurrent_options_visited": all({r["source"] for r in translated if r["slot"] == slot} == values for slot, values in expected.items()),
            "settings_all_option_values_translated": len(translated) == 13 and all(r["target"] == translations.get(r["source"]) for r in translated),
            "settings_options_active_no_overflow": len(translated) == 13 and all(r["active"] and not r["overflow"] for r in translated),
            "settings_each_slot_toggle_original": {r["slot"] for r in original} == set(expected) and all(r["target"] == r["source"] for r in original),
            "settings_each_slot_toggle_restored": {r["slot"] for r in restored} == set(expected) and all(r["target"] == translations.get(r["source"]) for r in restored),
            "settings_cancelled_without_applying": "CANCELLED\tTrue" in report and "SCOPES_RETAINED\tTrue" in report and "STATUS\tCOMPLETE" in report and "FAILURE\t" not in report}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=Path("runtime/evidence"))
    parser.add_argument("--translations", type=Path)
    parser.add_argument("--require-settings-options", action="store_true")
    arguments = parser.parse_args()
    directory = arguments.evidence
    menu = parse_objects(directory / "menu-texts.txt")
    settings = parse_objects(directory / "settings-texts.txt")
    visible_menu = [item for item in menu if item["active"]]
    visible_settings = [item for item in settings if item["active"]]
    expected_settings = None
    if arguments.translations:
        translations = {row["source"]: row["target"] for row in json.loads(arguments.translations.read_text(encoding="utf-8"))}
        expected_settings = {translations[key] for key in ("Graphics", "Audio", "Gameplay")}
    menu_report = (directory / "menu-texts.txt").read_text(encoding="utf-8-sig")
    assertions = evaluate(menu, settings, menu_report, (directory / "BepInEx.log").read_text(encoding="utf-8-sig"), expected_settings)
    if "FULL_CHINESE_GLYPHS=" in menu_report:
        assertions["full_translation_chinese_glyphs_available"] = "FULL_CHINESE_GLYPHS=True" in menu_report
    if "FROZEN_CACHE_CASES=" in menu_report:
        assertions["frozen_long_dialogue_dynamic_cache_cases"] = "FROZEN_CACHE_CASES=True" in menu_report
    if "SAVE_WRITE_GUARD_ACTIVE=" in menu_report:
        assertions["save_write_guard_active"] = "SAVE_WRITE_GUARD_ACTIVE=True" in menu_report
    if arguments.require_settings_options:
        if not arguments.translations:
            raise SystemExit("逐档选项验证需要正式译文")
        assertions.update(evaluate_settings_options((directory / "settings-options.txt").read_text(encoding="utf-8"), translations))
    if (directory / "original-menu-texts.txt").exists():
        original = {item.get("text") for item in parse_objects(directory / "original-menu-texts.txt") if item["active"]}
        restored = {item.get("text") for item in parse_objects(directory / "restored-menu-texts.txt") if item["active"]}
        log = (directory / "BepInEx.log").read_text(encoding="utf-8-sig")
        assertions.update(evaluate_toggle(original, restored, log))
    summary = {
        "test_level": "真实游戏 UI 集成探针；不是完整游玩 E2E",
        "assertions": assertions,
        "passed": all(assertions.values()),
        "visible_menu": visible_menu,
        "visible_settings": visible_settings,
        "limits": ["未点击开始/继续按钮；游戏可能自动加载隔离存档副本", "未验收对白和资料页面的像素排版", "后台组件检查不能证明全剧情分支覆盖"],
    }
    (directory / "verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": summary["passed"], "assertions": assertions}, ensure_ascii=False, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
