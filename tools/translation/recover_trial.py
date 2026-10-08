"""从已冻结的真实 API 响应恢复对齐译文，不发送请求或改写模型措辞。"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "translation" / "trial-2026-10-09"
NUMBERED = re.compile(r"^([0-9]+)\.(.*)$")


def numbered_rows(content: str, require_wrapper: bool = False) -> list[tuple[int, str]]:
    """只接受完整编号行；不能靠忽略未知行掩盖漏译或解释文字。"""
    blocks = re.findall(r"<textarea>\s*([\s\S]*?)\s*</textarea>", content)
    if blocks:
        content = blocks[-1]
    elif require_wrapper:
        raise ValueError("原请求缺少明确的源文 textarea")
    rows = []
    for line in content.strip().splitlines():
        match = NUMBERED.fullmatch(line.strip())
        if not match or not match[2].strip():
            raise ValueError("响应含非编号行或空译文，拒绝恢复")
        rows.append((int(match[1]), match[2]))
    if not rows or [number for number, _ in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("编号缺失、重复或乱序，拒绝恢复")
    return rows


def split_speaker(text: str) -> dict:
    speaker = re.fullmatch(r"\[([^\]]+)\](.*)", text)
    return {"name": speaker[1], "message": speaker[2]} if speaker else {"message": text}


def restore_batch(inputs: list[dict], events: list[dict], model: str) -> tuple[list[dict], list[int]]:
    """按冻结请求的真实原文匹配片段，歧义、漏行、重复覆盖均拒绝。"""
    expected = [("[" + item["name"] + "]" if item.get("name") else "") + item["message"] for item in inputs]
    started = {event["request_index"]: event for event in events if event["event"] == "started"}
    restored = {}
    used = []
    for event in events:
        if event["event"] != "completed" or event.get("status_code") != 200 or event.get("model") != model:
            continue
        request = started[event["request_index"]]["request_body"]
        source = numbered_rows(request["messages"][-1]["content"], require_wrapper=True)
        source_texts = [text for _, text in source]
        matches = [index for index in range(len(expected) - len(source) + 1)
                   if expected[index:index + len(source)] == source_texts]
        if not matches:
            continue
        if len(matches) != 1:
            raise ValueError("请求原文在批次内不唯一，拒绝恢复")
        payload = json.loads(event["response_body"])
        response = payload["choices"][0]["message"].get("content", "")
        target = numbered_rows(response)
        if [number for number, _ in source] != [number for number, _ in target]:
            raise ValueError("输入输出编号集合不同，拒绝恢复")
        for offset, (_, text) in enumerate(target):
            index = matches[0] + offset
            if index in restored:
                raise ValueError("多个响应覆盖同一条原文，需人工选定版本")
            restored[index] = split_speaker(text)
        used.append(event["request_index"])
    if len(restored) != len(inputs):
        raise ValueError(f"本批次冻结响应不完整：{len(restored)}/{len(inputs)}")
    result = [restored[index] for index in range(len(inputs))]
    if any(not re.search(r"[\u3400-\u9fff]", item["message"]) for item in result):
        raise ValueError("冻结响应存在无中文条目，拒绝视为完整试译")
    return result, used


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--accept-recovered", action="store_true", help="恢复现成执行器结果，原输出保留独立备份")
    args = parser.parse_args()
    provider = json.loads((ROOT / "translation" / "provider.json").read_text(encoding="utf-8"))
    if args.candidate not in provider["models"]:
        parser.error("候选模型未在公开配置中登记")
    manifest = json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))
    batch = next((item for item in manifest["batches"] if item["id"] == args.batch), None)
    if batch is None:
        parser.error("未知样本批次")
    inputs = json.loads((TRIAL / "inputs" / batch["file"]).read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (TRIAL / "api-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    rows, used = restore_batch(inputs, events, provider["models"][args.candidate])
    output = TRIAL / "recovered" / args.candidate / batch["file"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    proof = {"candidate": args.candidate, "batch": args.batch, "count": len(rows),
             "api_request_indices": used, "additional_model_calls": 0,
             "method": "从冻结响应按真实源文、完整编号和顺序恢复；未改译文措辞"}
    output.with_suffix(".provenance.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.accept_recovered:
        destination = TRIAL / "outputs" / args.candidate
        target_file = destination / args.batch / batch["file"]
        backup = target_file.with_suffix(".before-recovery.json")
        if backup.exists():
            parser.error("已有恢复备份，拒绝重复覆盖")
        if target_file.exists():
            target_file.rename(backup)
        target_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run_path = destination / "run.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        for item in run["batches"]:
            if item["batch"] == args.batch:
                item.update({"exit_code": 0, "validation": {"passed": True, "expected_count": len(inputs),
                             "output_count": len(rows), "new_model_calls": len(used), "frozen_response_recovery": True}})
        run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, ensure_ascii=True))


if __name__ == "__main__":
    main()
