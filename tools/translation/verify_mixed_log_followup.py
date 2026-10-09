"""使用真实XUnity消费者核验完整混合矩阵及既有回归，输出独立本轮证据。"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

from prepare_dialogue_log_followup import ROOT, read, save
from prepare_mixed_log_followup import BUILD, OUT, FULL


def run_suite(filename):
    path = OUT / filename
    command = [str(ROOT / "runtime/build/VerifyRecursiveUiRules.exe"),
               str(ROOT / "runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll"),
               str(FULL / "dynamic-rules.json"), str(FULL / "translations.json"), str(path)]
    process = subprocess.run(command, capture_output=True, cwd=ROOT, timeout=180)
    result_path = BUILD / (path.stem + "-result.jsonl")
    result_path.write_bytes(process.stderr + process.stdout)
    rows = [json.loads(line) for line in (process.stderr + process.stdout).decode("utf-8-sig").splitlines()]
    summary = rows[-1]
    if (process.returncode or not summary.get("actual_recursive_xunity_consumer_passed")
            or summary.get("count") != len(read(path)) or len(rows) != 1):
        raise ValueError("真实消费者失败：" + filename + "；见" + str(result_path.relative_to(ROOT)))
    print(filename + "：" + str(summary["count"]) + "项通过", flush=True)
    return filename, summary


def main():
    filenames = ["mixed-log-tests.json", "mixed-log-pair-tests.json", "dialogue-log-followup-tests.json",
                 "dialogue-log-depth-tests.json", "lead-followup-tests.json", "map-ui-tests.json",
                 "timeline-followup-tests.json", "nested-belief-followup-tests.json", "dynamic-ui-tests.json",
                 "notification-ui-tests.json"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = dict(executor.map(run_suite, filenames))
    import hashlib
    artifacts = [FULL / "translations.json", FULL / "dynamic-rules.json", OUT / "mixed-log-rules.json",
                 OUT / "mixed-log-translations.json", OUT / "mixed-log-tests.json", OUT / "mixed-log-pair-tests.json",
                 OUT / "knight-guard-corrections.json", ROOT / "tools/translation/prepare_mixed_log_followup.py"]
    proof = {"passed": True, "suites": results, "total_cases": sum(row["count"] for row in results.values()),
             "matrix": read(BUILD / "manifest.json"),
             "artifact_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
             "limits": ["使用真实XUnity逆序首匹配消费者；未启动游戏或宣称全剧情游玩",
                        "覆盖有限格式分支和当前已审资源，不宣称任意未知条目或无限重复序列都可翻译",
                        "矩阵包含不可能同时发生的剧情条目，仅检验格式衔接"]}
    save(ROOT / "runtime/evidence/mixed-log-offline-verification.json", proof)
    print(json.dumps({"passed": True, "total_cases": proof["total_cases"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
