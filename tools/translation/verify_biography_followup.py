"""用真实XUnity首匹配递归消费者验证全部简介保序子集，记录精确输入哈希。"""

import hashlib
import json
import subprocess

from prepare_biography_followup import ROOT, save


def main():
    full = ROOT / "translation/sol-full-2026-10-09"
    build = ROOT / "runtime/build/biography-followup"
    cases_path = build / "consumer-tests.json"
    executable = ROOT / "runtime/build/VerifyRecursiveUiRules.exe"
    core = ROOT / "runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    process = subprocess.run([str(executable), str(core), str(full / "dynamic-rules.json"),
                              str(full / "translations.json"), str(cases_path)],
                             capture_output=True, cwd=ROOT, timeout=120)
    output = process.stderr + process.stdout
    (build / "consumer-result.jsonl").write_bytes(output)
    results = [json.loads(line) for line in output.decode("utf-8-sig").splitlines()]
    if (process.returncode or len(results) != 1 or not results[0].get("actual_recursive_xunity_consumer_passed")
            or results[0].get("count") != len(cases)):
        raise ValueError("真实人物简介递归消费失败：runtime/build/biography-followup/consumer-result.jsonl")
    artifacts = [full / "translations.json", full / "dynamic-rules.json", cases_path, executable, core,
                 ROOT / "translation/supplemental/bio-runtime-aliases.json",
                 ROOT / "translation/supplemental/biography-followup-rules.json",
                 ROOT / "runtime/evidence/biography-source-audit.json"]
    proof = {"passed": True, "suite": results[0], "positive_cases": sum(row["target"] is not None for row in cases),
             "unknown_rejection_cases": sum(row["target"] is None for row in cases),
             "artifact_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in artifacts},
             "limits": ["真实.NET/XUnity递归消费者验证，遵守逆序首匹配及64层上限", "不是游戏界面或剧情解锁的端到端测试"]}
    save(ROOT / "runtime/evidence/biography-offline-verification.json", proof)
    print(json.dumps(proof, ensure_ascii=False))


if __name__ == "__main__":
    main()
