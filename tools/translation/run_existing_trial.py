"""配置并调用现成 AiNiee-Next 完成有限试译，不实现翻译调度。"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from check_provider import load_key

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "translation" / "trial-2026-10-09"
RUNNER = ROOT / "tools" / "translation" / "upstream-runner"
PYTHON = ROOT / "runtime" / "vendor" / "AiNiee-Next" / ".venv" / "Scripts" / "python.exe"
PRICES = {
    "deepseek-v4-pro-0813": {"input": 9, "output": 27},
    "deepseek-v4.1-flash": {"input": 2, "output": 8},
    "ZHIPU/GLM-5.3-Flash": {"input": 0.8, "output": 2.8},
    "qwen-mt-plus": {"input": 1.8, "output": 5.4},
}


def mask(text: str, key: str) -> str:
    return re.sub(r"sk-[A-Za-z0-9._~+/=-]+", "[已隐藏密钥]", text.replace(key, "[已隐藏密钥]"))


def completed_calls(model: str) -> int:
    ledger = TRIAL / "api-ledger.jsonl"
    if not ledger.exists():
        return 0
    return sum(row.get("event") == "completed" and row.get("status_code") == 200 and row.get("model") == model
               for row in (json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()))


def validate_batch(input_file: Path, output_directory: Path, new_model_calls: int) -> dict:
    """实际调用、数量与中文结果一起核对，不能只信 CLI 退出码。"""
    source = json.loads(input_file.read_text(encoding="utf-8"))
    output_file = output_directory / input_file.name
    if not output_file.is_file():
        return {"passed": False, "reason": "没有生成译文文件", "new_model_calls": new_model_calls}
    target = json.loads(output_file.read_text(encoding="utf-8-sig"))
    same_count = len(source) == len(target)
    untranslated = [index for index, item in enumerate(target)
                    if not item.get("message", "").strip() or not re.search(r"[\u3400-\u9fff]", item["message"])]
    return {"passed": new_model_calls > 0 and same_count and not untranslated,
            "new_model_calls": new_model_calls, "expected_count": len(source), "output_count": len(target),
            "no_chinese_indices": untranslated}


def trial_complete(previous: dict, manifest: dict) -> bool:
    """全部预期批次完成才算结束，部分批次通过仍可继续未跑的批次。"""
    expected = {item["id"] for item in manifest["batches"]}
    batches = previous.get("batches", [])
    actual = {item["batch"] for item in batches}
    return bool(expected) and actual == expected and len(batches) == len(expected) and all(
        item.get("exit_code") == 0 and item.get("validation", {}).get("passed") for item in batches
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=["deepseek_pro", "deepseek_flash", "glm_flash", "qwen_mt"])
    parser.add_argument("--resume-failed", action="store_true", help="仅继续先前失败的候选，保留旧日志与运行记录")
    args = parser.parse_args()
    provider = json.loads((ROOT / "translation" / "provider.json").read_text(encoding="utf-8"))
    manifest = json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))
    model = provider["models"][args.candidate]
    destination = TRIAL / "outputs" / args.candidate
    previous = None
    if destination.exists():
        if not args.resume_failed or not (destination / "run.json").is_file():
            parser.error("该候选已有输出目录，拒绝重复付费；仅经审阅后显式继续失败运行")
        previous = json.loads((destination / "run.json").read_text(encoding="utf-8"))
        if trial_complete(previous, manifest):
            parser.error("该候选先前已完成，不允许重复付费运行")
        history = destination / "history"
        history.mkdir(exist_ok=True)
        history_file = history / f"attempt-{len(list(history.glob('attempt-*.json'))) + 1}.json"
        history_file.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        destination.mkdir(parents=True)
    key = load_key(ROOT / provider["credential_file"])
    environment = os.environ.copy()
    environment.update({"AINIEE_WEB_TASK_API_KEY": key,
                        "AINIEE_API_AUDIT_LEDGER": str(TRIAL / "api-ledger.jsonl"),
                        "AINIEE_MAX_API_POSTS": "24", "AINIEE_MAX_OUTPUT_TOKENS": "4096",
                        "AINIEE_TOTAL_BUDGET_CNY": "4.75",
                        "AINIEE_API_PRICES_JSON": json.dumps(PRICES),
                        "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    results = []
    for batch in manifest["batches"]:
        old_batch = next((item for item in previous["batches"] if item["batch"] == batch["id"]), None) if previous else None
        if old_batch and old_batch["exit_code"] == 0 and old_batch.get("validation", {}).get("passed"):
            results.append(old_batch)
            continue
        profile = "elsinore-" + args.candidate + "-" + batch["id"]
        prepare = [str(PYTHON), str(RUNNER / "prepare_config.py"),
                   "--base-url", provider["openai_compatible_url"], "--model", model,
                   "--profile", profile, "--max-output-tokens", "4096",
                   "--prompt", str(TRIAL / "system-prompt.txt"), "--style", str(TRIAL / "writing-style.txt"),
                   "--rules", str(TRIAL / "rules" / (batch["id"] + ".json")),
                   "--thinking", "true" if args.candidate == "glm_flash" else "false"]
        process_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.run(prepare, cwd=ROOT, check=True, capture_output=True, creationflags=process_flags)
        command = [str(PYTHON), str(RUNNER / "launch.py"), "translate", str(TRIAL / "inputs" / batch["file"]),
                   "--execution-mode", "default_api", "--type", "Vnt", "--source", "英语",
                   "--target", "简体中文", "--profile", profile, "--rules-profile", profile,
                   "--output", str(destination / batch["id"]), "--threads", "1", "--retry", "0",
                   "--rounds", "1", "--timeout", "90", "--lines", "15", "--pre-lines", "0",
                   "--failover", "off", "--yes"]
        print(json.dumps({"candidate": args.candidate, "batch": batch["id"], "state": "started"}, ensure_ascii=True), flush=True)
        before_calls = completed_calls(model)
        try:
            completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, timeout=240, creationflags=process_flags)
            output = mask(completed.stdout.decode("utf-8", errors="replace"), key)
            code = completed.returncode
        except subprocess.TimeoutExpired as error:
            output = mask((error.stdout or b"").decode("utf-8", errors="replace"), key)
            code = -1
        log = destination / (batch["id"] + ".log")
        if log.exists():
            old_log = log.with_name(log.stem + f".before-{len(list((destination / 'history').glob('attempt-*.json')))}.log")
            log.rename(old_log)
        log.write_text(output, encoding="utf-8")
        validation = validate_batch(TRIAL / "inputs" / batch["file"], destination / batch["id"], completed_calls(model) - before_calls)
        if code == 0 and not validation["passed"]:
            code = 1
        results.append({"batch": batch["id"], "exit_code": code, "validation": validation})
        print(json.dumps({"candidate": args.candidate, "batch": batch["id"], "exit_code": code, "validation": validation}, ensure_ascii=True), flush=True)
        if code != 0:
            break
    (destination / "run.json").write_text(json.dumps({"model": model, "batches": results,
                 "executor": "AiNiee-Next", "upstream_commit": "b0883c9f806984571d8f9fe8c4345425d1e6fe83"},
                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if any(item["exit_code"] != 0 for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
