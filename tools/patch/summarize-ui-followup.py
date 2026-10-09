"""绑定本轮UI证据、正式安装与个人备份包；独立保留前轮字体几何验收。"""

import argparse
import hashlib
import json
from pathlib import Path
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
    menu = read(run / "verification.json")
    journal = read(run / "journal-analysis.json")
    lead = read(run / "lead-followup-analysis.json")
    map_proof = read(run / "map-followup-analysis.json")
    timeline = read(run / "timeline-followup-analysis.json")
    reflection = read(ROOT / "runtime/evidence/timeline-reflection-verification.json")
    assert reflection["passed"] and reflection["exact_method_signatures"] == 13
    assert len(reflection["clock_fixtures"]) == 5 and reflection["legacy_six_hour_offset_reproduced"]
    process = read(run / "process.json")
    save = read(run / "save-protection.json")
    proof = read(ROOT / "translation/sol-full-2026-10-09/verification.json")
    installed = read(ROOT / "runtime/evidence/full-installed-files.json")
    assert all(item["passed"] for item in (menu, journal, lead, map_proof))
    assert timeline["display_matches_frozen_translation"] and timeline["f8_source_complete"]
    assert process["exit_code"] == 0 and not process["main_window_detected"]
    assert process["batch_mode_confirmed"] and process["wwise_suspend_success"]
    assert save["frozen_source_unchanged"]
    assert save["original_save_files_unchanged"] or not save["original_save_comparison_conclusive"]
    assert proof["count"] == 16861 and proof["dynamic_format_rules"] == 121
    assert proof["id_count_order_source_hashes_and_markers_passed"]
    assert installed["dictionary_count"] == proof["count"] and Path(installed["game_path"]) == GAME
    assert "ElsinoreHan Translation Toggle 1.3.0" in (run / "BepInEx.log").read_text(encoding="utf-8-sig")
    assert not (TEST_GAME / "BepInEx/plugins/ElsinoreHan.RuntimeProbe.dll").exists()
    assert not (TEST_GAME / "steam_appid.txt").exists()
    assert digest(TEST_GAME / "BepInEx/config/BepInEx.cfg") == digest(run / "loader-config-before.bin")
    originals = read(ROOT / "runtime/evidence/original-game-hashes.json")
    assert all(digest(GAME / row["path"]) == row["sha256"].lower() for row in originals)
    audit = read(ROOT / "analysis/ui-audit/notification-source-audit.json")["actual_component_verification"]
    for file, expected in audit["artifact_sha256"].items():
        assert digest(ROOT / file) == expected, file
    suites = {}
    offline = ROOT / "runtime/evidence/headless/followup-offline-2026-10-10"
    for name in ("lead-followup", "map-ui", "timeline-followup", "nested-belief-followup", "dynamic-ui", "notification-ui"):
        suite = read(offline / (name + "-summary.json"))
        assert suite["actual_recursive_xunity_consumer_passed"]
        assert suite["count"] == len(read(ROOT / "translation/supplemental" / (name + "-tests.json")))
        suites[name] = suite["count"]
    assert sum(suites.values()) == 1538
    archive = ROOT / "runtime/package/ElsinoreHan-Sol.zip"
    files = {}
    with zipfile.ZipFile(archive) as package_zip:
        entries = package_zip.namelist()
        assert len(entries) == 39
        assert not any("RuntimeProbe" in file or "api-key" in file or file.endswith(".save") for file in entries)
        for relative in ("BepInEx/plugins/ElsinoreHan.TranslationToggle.dll",
                         "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt",
                         "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt"):
            values = {"installed": digest(GAME / relative), "tested": digest(TEST_GAME / relative),
                      "package": digest(PACKAGE / relative), "zip": hashlib.sha256(package_zip.read(relative)).hexdigest()}
            assert len(set(values.values())) == 1, relative
            files[relative] = values
    assert files["BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt"]["installed"] == proof["dictionary_sha256"]
    assert files["BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt"]["installed"] == proof["dynamic_dictionary_sha256"]
    summary = {"plugin_version": "1.3.0", "run_id": args.run_id, "installed": True,
               "dictionary_entries": proof["count"], "total_dynamic_rules": proof["dynamic_format_rules"],
               "recursive_ui_rules": proof["recursive_ui_rules"], "recursive_consumer_suites": suites,
               "lead": lead, "map": map_proof, "timeline": timeline, "timeline_reflection": reflection,
               "journal_component_passed": journal["passed"], "journal_checks": journal["checks"],
               "all_history_indices": len(journal["log_entries"]), "closeup_documents": len(journal["closeup_batch"]),
               "known_characters_layout": len(journal["character_layouts"]), "menu_checks": menu["assertions"],
               "process": process, "save_protection": save, "files": files,
               "installed_backup": installed["backup_path"], "zip_entries": len(entries), "zip_sha256": digest(archive),
               "original_game_binaries_unchanged": True, "temporary_probe_and_appid_removed": True,
               "test_loader_config_restored_byte_exact": True,
               "report_sha256": {name: digest(run / name) for name in ("journal-ui.txt", "lead-followup.tsv", "map-followup.tsv", "timeline-followup.tsv")},
               "consumer_tests_sha256": {name: digest(ROOT / "translation/supplemental" / (name + "-tests.json")) for name in suites},
               "offline_tests": {"export": 15, "lead_sources": 5, "map_sources": 7, "journal_verifier": 37,
                                 "menu_verifier": 22, "launch_preflight": 7, "lead_verifier": 8, "map_verifier": 15,
                                 "timeline_verifier": 29},
               "limits": ["真实页面、组件事件和格式器重放分别记账；重放不代表已获得具体剧情",
                          "不注入物理按键，不确认地图移动，不验收像素渲染或全剧情分支",
                          "字体未改；本轮未重复前轮字体几何和逐档设置检查"]}
    destination = ROOT / "runtime/evidence/ui-followup-verification.json"
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": True, "run_id": args.run_id, "installed": True, "consumers": sum(suites.values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
