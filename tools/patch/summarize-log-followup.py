"""绑定本轮日志资源覆盖、F8布局、称号及正式安装；保留历史阶段摘要。"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
GAME = Path("D:/SteamLibrary/steamapps/common/Elsinore")
TEST_GAME = ROOT / "runtime/game-test/settings-options"
PACKAGE = ROOT / "runtime/package/ElsinoreHan-Sol"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args()
    run = ROOT / "runtime/evidence/headless" / args.run_id
    components = {name: read(run / (name + "-analysis.json")) for name in
                  ("journal", "lead-followup", "map-followup", "timeline-followup", "log-scroll-anchor")}
    assert all(item["passed"] for item in components.values())
    menu = read(run / "verification.json")
    process = read(run / "process.json")
    save = read(run / "save-protection.json")
    proof = read(ROOT / "translation/sol-full-2026-10-09/verification.json")
    assert menu["passed"] and process["exit_code"] == 0 and not process["main_window_detected"]
    assert process["batch_mode_confirmed"] and process["wwise_suspend_success"]
    assert save["frozen_source_unchanged"] and (save["original_save_files_unchanged"] or not save["original_save_comparison_conclusive"])
    assert proof["count"] == 16866 and proof["dynamic_format_rules"] == 132 and proof["recursive_ui_rules"] == 108
    assert "ElsinoreHan Translation Toggle 1.4.0" in (run / "BepInEx.log").read_text(encoding="utf-8-sig")
    for relative in ("BepInEx/plugins/ElsinoreHan.RuntimeProbe.dll", "steam_appid.txt"):
        assert not (TEST_GAME / relative).exists()
    assert digest(TEST_GAME / "BepInEx/config/BepInEx.cfg") == digest(run / "loader-config-before.bin")
    original = read(ROOT / "runtime/evidence/original-game-hashes.json")
    assert all(digest(GAME / row["path"]) == row["sha256"].lower() for row in original)
    rows = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    terms = [row for row in rows if re.search("playmaster", row["source"], re.I)]
    assert len(terms) == 33 and all("戏剧大师" in row["target"] for row in terms)
    audit = read(ROOT / "analysis/ui-audit/notification-source-audit.json")["actual_component_verification"]
    for path, sha in audit["artifact_sha256"].items():
        assert digest(ROOT / path) == sha, path
    offline = ROOT / "runtime/evidence/headless/log-followup-offline-2026-10-10"
    suites = {}
    for name in ("dialogue-log-standard", "dialogue-log-depth", "lead-followup", "map-ui", "timeline-followup",
                 "nested-belief-followup", "dynamic-ui", "notification-ui"):
        result = read(offline / (name + "-summary.json"))
        assert result["actual_recursive_xunity_consumer_passed"]
        suites[name] = result["count"]
    assert sum(suites.values()) == 23116
    files = {}
    archive = ROOT / "runtime/package/ElsinoreHan-Sol.zip"
    with zipfile.ZipFile(archive) as package_zip:
        entries = package_zip.namelist()
        assert len(entries) == 39
        assert not any("RuntimeProbe" in name or "api-key" in name or name.endswith(".save") for name in entries)
        for relative in ("BepInEx/plugins/ElsinoreHan.TranslationToggle.dll",
                         "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt", "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt"):
            values = {"installed": digest(GAME / relative), "tested": digest(TEST_GAME / relative),
                      "package": digest(PACKAGE / relative), "zip": hashlib.sha256(package_zip.read(relative)).hexdigest()}
            assert len(set(values.values())) == 1, relative
            files[relative] = values
    assert files["BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt"]["installed"] == proof["dictionary_sha256"]
    assert files["BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt"]["installed"] == proof["dynamic_dictionary_sha256"]
    installed = read(ROOT / "runtime/evidence/full-installed-files.json")
    assert installed["dictionary_count"] == proof["count"]
    summary = {"run_id": args.run_id, "plugin_version": "1.4.0", "installed": True,
               "dictionary_entries": proof["count"], "dynamic_rules": proof["dynamic_format_rules"],
               "components": components, "consumer_suites": suites, "canonical_playmaster": "戏剧大师",
               "playmaster_source_count": len(terms), "files": files, "installed_backup": installed["backup_path"],
               "zip_entries": len(entries), "zip_sha256": digest(archive), "process": process, "save_protection": save,
               "original_game_binaries_unchanged": True, "temporary_probe_cleaned": True, "test_loader_config_restored": True,
               "limits": ["全资源单句/相邻/同人续行与静态场景格式压力，包含互斥分支，不能冒充全剧情E2E",
                          "F8保持同一硬换行段落起点附近；长段内部非逐词定位，换行结构变化或历史变动保守跳过",
                          "真实TMP局部坐标和共享F8入口验证；未注入物理键盘或验收像素渲染，字体参数未改"]}
    destination = ROOT / "runtime/evidence/log-followup-verification.json"
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": True, "installed": True, "run_id": args.run_id, "consumers": sum(suites.values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
