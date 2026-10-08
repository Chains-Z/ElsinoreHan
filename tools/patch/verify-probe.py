"""核查真实游戏探针记录，防止菜单词表漏译和中文溢出回归。"""

from __future__ import annotations

import argparse
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


def evaluate(menu: list[dict], settings: list[dict], menu_text: str, log: str) -> dict[str, bool]:
    """只有目标界面确实出现时，才评估该页的文字溢出。"""
    visible_menu = [item for item in menu if item["active"]]
    visible_settings = [item for item in settings if item["active"]]
    expected = {"继续游戏", "设置", "退出游戏"}
    actual = {item.get("text") for item in visible_menu}
    settings_opened = {"Graphics", "Audio", "Gameplay"} <= {item.get("text") for item in visible_settings}
    return {
        "menu_labels_all_translated": expected <= actual,
        "menu_labels_no_overflow": expected <= actual and all(not item.get("overflow", True) for item in visible_menu if item.get("text") in expected),
        "menu_no_original_labels": not ({"Continue Game", "Quit Game", "Settings"} & actual),
        "chinese_glyphs_available": "GLYPHS_继续游戏设置退出=True" in menu_text,
        "settings_pointer_navigation_logged": "EventSystem" in log,
        "settings_page_opened": settings_opened,
        "settings_visible_texts_no_overflow": settings_opened and all(not item.get("overflow", True) for item in visible_settings),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=Path("runtime/evidence"))
    arguments = parser.parse_args()
    directory = arguments.evidence
    menu = parse_objects(directory / "menu-texts.txt")
    settings = parse_objects(directory / "settings-texts.txt")
    visible_menu = [item for item in menu if item["active"]]
    visible_settings = [item for item in settings if item["active"]]
    assertions = evaluate(menu, settings, (directory / "menu-texts.txt").read_text(encoding="utf-8-sig"), (directory / "BepInEx.log").read_text(encoding="utf-8-sig"))
    summary = {
        "test_level": "真实游戏 UI 集成探针；不是完整游玩 E2E",
        "assertions": assertions,
        "passed": all(assertions.values()),
        "visible_menu": visible_menu,
        "visible_settings": visible_settings,
        "limits": ["未点击继续游戏，未进入存档", "未验收对白和资料页面", "设置页尚未全量汉化"],
    }
    (directory / "verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": summary["passed"], "assertions": assertions}, ensure_ascii=False, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
