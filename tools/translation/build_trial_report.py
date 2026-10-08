"""离线核对真实试译的来源、冻结响应与格式，并生成完整对照表。"""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from recover_trial import restore_batch

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "translation" / "trial-2026-10-09"
LABELS = {
    "deepseek_pro": "DeepSeek Pro",
    "deepseek_flash": "DeepSeek Flash",
    "glm_flash": "GLM Flash",
    "qwen_mt": "Qwen-MT Plus",
}
ANONYMOUS = {"deepseek_pro": "first", "glm_flash": "second", "qwen_mt": "third", "deepseek_flash": "fourth"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def markers(text: str) -> Counter:
    """标签与占位符保持数量一致；语义覆盖范围仍需人工审读。"""
    return Counter(re.findall(r"</?[A-Za-z][^>]*>|\{[^{}]+\}|%(?:\d+\$)?[sdif]", text))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    from opencc import OpenCC

    manifest = load(TRIAL / "manifest.json")
    provider = load(ROOT / "translation" / "provider.json")
    ledger = [json.loads(line) for line in (TRIAL / "api-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    completed = [row for row in ledger if row["event"] == "completed" and row.get("status_code") == 200]
    started = [row for row in ledger if row["event"] == "started"]
    rows = [{"id": item["id"], "source": item["message"], "speaker": item["name"],
             "context": item["context"], "register": item["register"], "targets": {}}
            for item in manifest["entries"]]
    assert len({row["id"] for row in rows}) == manifest["count"]
    source_checks = []
    for entry in manifest["entries"]:
        source = load(TRIAL / "inputs" / entry["file"])[entry["index"]]
        assert source["message"] == entry["message"]
        assert hashlib.sha256(source["message"].encode("utf-8")).hexdigest() == entry["source_text_sha256"]
        source_checks.append(entry["id"])
    conversion = OpenCC("t2s")
    candidates = {}
    for alias, label in LABELS.items():
        checks, notices, used_requests = [], [], []
        for batch in manifest["batches"]:
            inputs = load(TRIAL / "inputs" / batch["file"])
            output = load(TRIAL / "outputs" / alias / batch["id"] / batch["file"])
            frozen, indices = restore_batch(inputs, ledger, provider["models"][alias])
            assert len(output) == len(inputs) == batch["count"]
            used_requests.extend(indices)
            for entry in (item for item in manifest["entries"] if item["batch"] == batch["id"]):
                target = output[entry["index"]]["message"]
                assert target == frozen[entry["index"]]["message"], (alias, entry["id"], "输出与冻结响应不符")
                check = {"id": entry["id"], "nonempty_chinese": bool(re.search(r"[\u3400-\u9fff]", target)),
                         "markers_preserved": markers(target) == markers(entry["message"])}
                checks.append(check)
                if conversion.convert(target) != target:
                    notices.append({"id": entry["id"], "target": target, "t2s": conversion.convert(target)})
                next(row for row in rows if row["id"] == entry["id"])["targets"][alias] = target
        calls = [event for event in completed if event["request_index"] in used_requests]
        candidates[alias] = {"model": provider["models"][alias], "count": len(checks),
                             "api_request_indices": used_requests, "successful_requests": len(calls),
                             "prompt_tokens": sum(event["usage"]["prompt_tokens"] for event in calls),
                             "completion_tokens": sum(event["usage"]["completion_tokens"] for event in calls),
                             "cost_estimate_cny": sum(event["usage_cost_cny_without_cache_discount"] for event in calls),
                             "format_passed": all(check["nonempty_chinese"] and check["markers_preserved"] for check in checks),
                             "checks": checks, "simplification_review_notices": notices}
        anonymous = [{key: row[key] for key in ("id", "source", "speaker", "context", "register")} |
                     {"target": row["targets"][alias]} for row in rows]
        write_json(TRIAL / "review-input" / ("candidate-" + ANONYMOUS[alias] + ".json"), anonymous)
    verification = {"source_count": len(source_checks), "candidate_count": len(candidates),
                    "output_count": sum(item["count"] for item in candidates.values()),
                    "source_hashes_and_input_order_passed": True, "all_outputs_match_frozen_responses": True,
                    "started_requests": len(started), "successful_requests": len(completed),
                    "cost_estimate_cny": sum(event["usage_cost_cny_without_cache_discount"] for event in completed),
                    "cost_method": "按峰时单价与真实usage折算，未扣缓存及优惠；不含连通标题，不是实际账单",
                    "candidates": candidates,
                    "limitations": ["格式通过不代表意义和中文质量通过", "标签数量一致不证明强调范围一致",
                                    "简繁转换差异只作审读提示，不能机械判定错误", "静态来源未动态确认加载版本",
                                    "没有验证这些译文在游戏内显示", "这是单次40条小样，不能证明全量优劣"]}
    write_json(TRIAL / "verification.json", verification)
    write_json(TRIAL / "comparison.json", rows)
    table = ["# 四模型真实试译全文对照", "", "40条真实游戏原文，每个模型译文均来自冻结API响应，未润色。",
             "", "格式已核对；意义、语气和排版仍需审读。角色名属于背景元数据，正文按来源ID绑定。", ""]
    for index, row in enumerate(rows, 1):
        table.extend([f"## {index}. {row['id']}", "", f"说话人：{row['speaker']}", "", "原文：", "",
                      row["source"].replace("<", "&lt;").replace(">", "&gt;"), "", "| 模型 | 原始译文 |", "| --- | --- |"])
        for alias, label in LABELS.items():
            target = row["targets"][alias].replace("|", "\\|").replace("\n", "<br>").replace("<", "&lt;").replace(">", "&gt;")
            table.append(f"| {label} | {target} |")
        table.append("")
    (TRIAL / "comparison.md").write_text("\n".join(table), encoding="utf-8")
    print(json.dumps({"source_count": len(source_checks), "output_count": verification["output_count"],
                      "cost_estimate_cny": verification["cost_estimate_cny"],
                      "format_passed": {alias: item["format_passed"] for alias, item in candidates.items()},
                      "simplification_notice_counts": {alias: len(item["simplification_review_notices"]) for alias, item in candidates.items()}}, ensure_ascii=True))


if __name__ == "__main__":
    main()
