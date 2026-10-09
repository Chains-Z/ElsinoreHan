"""绑定混合日志消费者、真实离线API、存档保护与本轮安装/个人ZIP。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
GAME = Path("D:/SteamLibrary/steamapps/common/Elsinore")
TEST = ROOT / "runtime/game-test/settings-options"
PACKAGE = ROOT / "runtime/package/ElsinoreHan-Sol"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args()
    run = ROOT / "runtime/evidence/headless" / args.run_id
    offline = read(ROOT / "runtime/evidence/mixed-log-offline-verification.json")
    assert offline["passed"]
    for path, value in offline["artifact_sha256"].items():
        assert sha(ROOT / path) == value, path
    process = read(run / "process.json")
    save = read(run / "save-protection.json")
    assert process["exit_code"] == 0 and process["batch_mode_confirmed"] and process["wwise_suspend_success"]
    assert not process["main_window_detected"]
    assert save["original_save_files_unchanged"] and save["frozen_source_unchanged"]
    verification = read(run / "verification.json")
    assert verification["passed"]
    report = (run / "menu-texts.txt").read_text(encoding="utf-8-sig")
    cache_lines = [line for line in report.splitlines() if line.startswith("CACHE_CASE=")]
    assert len(cache_lines) == 111 and all(line.endswith("MATCH=True") for line in cache_lines)
    assert "FROZEN_CACHE_CASES=True COUNT=111" in report
    actual_ids = {line.split(" LENGTH=", 1)[0].split("=", 1)[1] for line in cache_lines}
    fixture = ROOT / "runtime/build/mixed-log-followup/cache-cases.tsv"
    expected_rows = {r["id"]: r for r in read(ROOT / "translation/supplemental/mixed-log-tests.json")}
    expected_rows.update({r["id"]: r for r in read(ROOT / "translation/sol-full-2026-10-09/translations.json")})
    frozen_rows = [line.split("\t") for line in fixture.read_text(encoding="utf-8").splitlines()]
    assert len(frozen_rows) == 111 and {fields[0] for fields in frozen_rows} == actual_ids
    for fields in frozen_rows:
        row = expected_rows[fields[0]]
        assert base64.b64decode(fields[1]).decode("utf-8") == row["source"]
        assert base64.b64decode(fields[2]).decode("utf-8") == row["target"]
    assert sha(TEST / "BepInEx/config/BepInEx.cfg") == sha(run / "loader-config-before.bin")
    assert not (TEST / "BepInEx/plugins/ElsinoreHan.RuntimeProbe.dll").exists()
    assert not (TEST / "steam_appid.txt").exists()
    assert all(sha(GAME / row["path"]) == row["sha256"].lower()
               for row in read(ROOT / "runtime/evidence/original-game-hashes.json"))
    source_review = read(ROOT / "runtime/evidence/mixed-log-source-review.json")
    assert sha(ROOT / source_review["il_evidence"]["path"]) == source_review["il_evidence"]["sha256"]
    proof = read(ROOT / "translation/sol-full-2026-10-09/verification.json")
    assert proof["count"] == 17027 and proof["dynamic_format_rules"] == 138
    files = {}
    archive = ROOT / "runtime/package/ElsinoreHan-Sol.zip"
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        assert len(names) == 39 and not any("RuntimeProbe" in s or "api-key" in s or s.endswith(".save") for s in names)
        for relative in ("BepInEx/plugins/ElsinoreHan.TranslationToggle.dll", "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt",
                         "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt"):
            hashes = {"installed": sha(GAME / relative), "tested": sha(TEST / relative), "package": sha(PACKAGE / relative),
                      "zip": hashlib.sha256(package.read(relative)).hexdigest()}
            assert len(set(hashes.values())) == 1, relative
            files[relative] = hashes
    assert files["BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt"]["installed"] == proof["dictionary_sha256"]
    assert files["BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt"]["installed"] == proof["dynamic_dictionary_sha256"]
    installed = read(ROOT / "runtime/evidence/full-installed-files.json")
    result = {"passed": True, "installed": True, "run_id": args.run_id, "plugin_version": "1.4.0",
              "dictionary_entries": proof["count"], "dynamic_rules": proof["dynamic_format_rules"],
              "new_terminal_lf_aliases": 161, "offline_consumer_cases": offline["total_cases"],
              "real_game_api_cases": len(cache_lines), "matrix": offline["matrix"], "files": files,
              "real_game_api_fixture_sha256": sha(fixture),
              "process": process, "save_protection": save, "installed_backup": installed["backup_path"],
              "zip_sha256": sha(archive), "temporary_probe_cleaned": True, "test_loader_config_restored": True,
              "original_game_binaries_unchanged": True,
              "title_targets": {"Bernardo": "丹麦贵族，骑士卫队队长", "Marcellus": "埃尔西诺骑士卫队成员"},
              "limits": ["覆盖真实格式入口、当前通知原子/人物简称及有限交叉矩阵，不宣称无限序列或未知资源永远可译",
                         "真实游戏中111项是离线TryTranslate消费及菜单F8，不称截图剧情已重新游玩",
                         "本轮没有重测日志滚动坐标、全部设置档位或字体像素；对应前轮证据保留",
                         "161条仅为通知末尾LF的精确源别名，不是重新翻译161段正文"]}
    destination = ROOT / "runtime/evidence/mixed-log-verification.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": True, "installed": True, "offline_cases": offline["total_cases"], "api_cases": len(cache_lines)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
