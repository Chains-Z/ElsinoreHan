"""用已登录的 Codex Sol 分批翻全文；无需额外 API Key，不使用百炼。"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "translation" / "sol-full-2026-10-09"
LOCK = threading.Lock()
STOP = threading.Event()


def markers(text):
    from collections import Counter
    return Counter(re.findall(r"</?[A-Za-z][^>]*>|\{(?:[A-Za-z_][A-Za-z0-9_.-]*|[0-9]+(?:,-?[0-9]+)?(?::[^{}]+)?)\}|%(?:\d+\$)?[sdif]", text))


def load_exclusions(directory):
    path = directory / "excluded-nontext.json"
    return {row["id"]: row["source_sha256"] for row in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else {}


def validate(source, value, excluded_sources=None):
    rows = value.get("translations", [])
    errors = []
    if [row.get("id") for row in rows] != [row["id"] for row in source]:
        errors.append("条目ID、顺序或数量不完整")
        return errors
    for original, target in zip(source, rows):
        text = target.get("target", "")
        if not isinstance(text, str) or not text.strip():
            errors.append(original["id"] + ": 空译文")
        elif markers(text) != markers(original["source"]):
            errors.append(original["id"] + ": 标签或占位符改变")
        elif (text.count("{"), text.count("}")) != (original["source"].count("{"), original["source"].count("}")):
            errors.append(original["id"] + ": 花括号包装改变")
        elif re.search(r"[A-Za-z]+\s+[A-Za-z]+", original["source"]) and not re.search(r"[\u3400-\u9fff]", text) and (excluded_sources or {}).get(original["id"]) != hashlib.sha256(original["source"].encode("utf-8")).hexdigest():
            errors.append(original["id"] + ": 普通文本没有中文")
    return errors


def prompt_for(source, glossary):
    return """你是本任务的中文游戏译者，模型必须是 GPT-6.1 Sol。只完成本批英文→简体中文翻译。
不要调用任何工具、执行命令、读取文件、联网或写Git；所有必需资料都在本提示。只按给定JSON Schema返回最终译文，不解释。
游戏Elsinore以奥菲莉娅为主角，改编自哈姆雷特，但不能套用原著改变本游戏身份。Lady Rosencrantz和Lady Guildenstern是女性。
忠实保留人称、否定、条件、时间状态、亲属关系、传闻和可能性，不补写原文没有的动作、关系、情绪或解释。
日常对白采用自然、顺口的现代中文，不用翻译腔或当代网络梗。只保留原文已有的少量古雅、戏剧感；祈祷、诗句和戏中戏适度凝练，不全文文言化。
结合句内和同一场景的真实台词理解省略与惯用语；多个场景、条件分支和返场彼此独立，不把数组所有条目想成同一次对话。
例如承接dead的he was. Is.仍表示过去和现在都死着，不译成活着；God forbid作为惯用否认不能机械当宗教禁令；on pause是状态，不擅改成主动按暂停。
同一固定人物译名一致，职位按上下文；不能把my blood擅定为兄弟。原文带<i>/<b>等标签时保持标签、数量和对应强调含义。
保留所有变量、占位符、转义及实际换行；不翻译ID、程序标识、逻辑条件。target字段只包含当前source的译文，不含说话人元数据或背景解释。
标点按自然中文处理，省略/结巴/断句保持人物表现。独立标题简洁，资料不能增强推测强度。译完先回读中文，再对照原文核对。
必须每个源ID各输出一次，顺序不变；不得漏译、用摘要代替、写TODO或返回英语作为翻译。
暂定术语表（source/target）：
""" + json.dumps(glossary, ensure_ascii=False) + "\n本批真实源文及只读语境：\n" + json.dumps(source, ensure_ascii=False)


def execute(batch, directory, glossary, executable):
    identifier = batch["id"]
    output = directory / "outputs" / (identifier + ".json")
    source = json.loads((directory / "inputs" / (identifier + ".json")).read_text(encoding="utf-8"))
    exclusions = load_exclusions(directory)
    if output.exists():
        value = json.loads(output.read_text(encoding="utf-8-sig"))
        if not validate(source, value, exclusions):
            return {"batch": identifier, "count": len(source), "state": "existing", "new_calls": 0}
        return {"batch": identifier, "state": "invalid_existing", "errors": validate(source, value, exclusions), "new_calls": 0}
    if STOP.is_set():
        return {"batch": identifier, "state": "not_started_after_failure", "new_calls": 0}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    temporary = directory / "raw" / (identifier + ".json")
    command = [executable, "exec", "-", "--model", "gpt-6.1-sol", "--ignore-user-config",
               "--sandbox", "read-only", "--ephemeral", "--color", "never", "--json",
               "-c", 'approval_policy="never"', "-c", 'model_reasoning_effort="low"',
               "-c", 'service_tier="default"', "--cd", str(ROOT),
               "--output-schema", str(directory / "output-schema.json"), "--output-last-message", str(temporary)]
    with LOCK:
        print(json.dumps({"batch": identifier, "state": "started", "count": len(source)}, ensure_ascii=True), flush=True)
    try:
        run = subprocess.run(command, input=prompt_for(source, glossary).encode("utf-8"),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags, timeout=900)
    except subprocess.TimeoutExpired as error:
        STOP.set()
        (directory / "raw" / (identifier + ".log")).write_bytes(error.stdout or b"")
        result = {"batch": identifier, "state": "timeout", "new_calls": 1, "count": len(source)}
        (directory / "audit" / (identifier + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    log = directory / "raw" / (identifier + ".log")
    log.write_bytes(run.stdout)
    usage = {}
    for line in run.stdout.decode("utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
            if event.get("type") == "turn.completed":
                usage = event.get("usage", {})
        except ValueError:
            pass
    result = {"batch": identifier, "model": "gpt-6.1-sol", "count": len(source), "new_calls": 1,
              "exit_code": run.returncode, "usage": usage, "source_sha256": hashlib.sha256((directory / "inputs" / (identifier + ".json")).read_bytes()).hexdigest()}
    if run.returncode == 0 and temporary.exists():
        value = json.loads(temporary.read_text(encoding="utf-8-sig"))
        result["errors"] = validate(source, value, exclusions)
        if not result["errors"]:
            output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result["state"] = "passed"
        else:
            result["state"] = "validation_failed"
    else:
        result["state"] = "execution_failed"
    if result["state"] != "passed":
        STOP.set()
    (directory / "audit" / (identifier + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with LOCK:
        print(json.dumps(result, ensure_ascii=True), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-dir", type=Path, default=DEFAULT)
    parser.add_argument("--limit-batches", type=int)
    parser.add_argument("--workers", type=int, default=3, choices=[1, 2, 3])
    args = parser.parse_args()
    directory = args.trial_dir.resolve()
    executable = shutil.which("codex.exe") or shutil.which("codex.cmd")
    if executable is None:
        raise SystemExit("未找到已安装的Codex入口")
    if executable.lower().endswith(".cmd"):
        candidates = list(Path(executable).parent.glob("node_modules/@openai/codex/node_modules/@openai/codex-*/vendor/*/codex/codex.exe"))
        if len(candidates) == 1:
            executable = str(candidates[0])
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    glossary = json.loads((directory / "glossary.json").read_text(encoding="utf-8"))["entries"]
    glossary = [{"source": row["source"], "target": row["target"]} for row in glossary]
    for name in ("outputs", "raw", "audit"):
        (directory / name).mkdir(exist_ok=True)
    batches = manifest["batches"]
    if args.limit_batches is not None:
        if args.limit_batches < 1:
            parser.error("批次数必须为正数")
        batches = batches[:args.limit_batches]
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(execute, batch, directory, glossary, executable) for batch in batches]
        for future in as_completed(futures):
            results.append(future.result())
    if any(row["state"] not in {"passed", "existing"} for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
