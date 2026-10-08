"""用真实游戏短句检查百炼权限与参数，保存脱敏证据，不承担全量翻译调度。"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_key(path: Path) -> str:
    """兼容纯密钥与带说明的文件，输出和异常都不包含文件正文。"""
    # 百炼新密钥可含点号分段，不能只取旧格式的前缀。
    keys = set(re.findall(r"sk-[A-Za-z0-9._~+/=-]+", path.read_text(encoding="utf-8-sig")))
    if len(keys) != 1:
        raise ValueError("密钥文件须包含且仅包含一把 sk- 开头的 Key")
    return keys.pop()


def safe_value(value, key: str):
    encoded = json.dumps(value, ensure_ascii=False).replace(key, "[已隐藏密钥]")
    return json.loads(re.sub(r"sk-[A-Za-z0-9._~+/=-]+", "[已隐藏密钥]", encoded))


def check_model(provider: dict, model: str, source: str, key: str) -> dict:
    endpoint = provider["openai_compatible_url"] + "/chat/completions"
    if not endpoint.startswith("https://" + provider["api_host"] + "/"):
        raise ValueError("接入地址与用户授权主机不一致")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": source}],
        "max_tokens": 512,
    }
    if model.startswith("qwen-mt"):
        payload["translation_options"] = {"source_lang": "English", "target_lang": "Chinese"}
    else:
        payload["messages"].insert(0, {
            "role": "system", "content": "把英文游戏文本译成简体中文，只输出译文，保留原意和标签。",
        })
        payload["enable_thinking"] = model.startswith("ZHIPU/")
        if payload["enable_thinking"]:
            payload["reasoning_effort"] = "low"
    request = urllib.request.Request(endpoint, json.dumps(payload).encode(), {
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
    })
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
            status = response.status
    except urllib.error.HTTPError as error:
        try:
            data = json.loads(error.read(16384))
        except (UnicodeError, json.JSONDecodeError):
            data = {"error": "上游返回非 JSON 错误"}
        status = error.code
    except (urllib.error.URLError, TimeoutError):
        status, data = 0, {"error": "请求超时或连接失败；不自动重试"}
    return safe_value({
        "scope": "真实短句接口检查，非质量盲评",
        "model": model, "http_status": status,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "source": source, "max_tokens": 512,
        "enable_thinking": payload.get("enable_thinking"), "response": data,
    }, key)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    provider = json.loads((ROOT / "translation" / "provider.json").read_text(encoding="utf-8"))
    if args.model not in provider["models"].values():
        parser.error("仅允许公开配置中已列明的候选模型")
    directory = ROOT / "translation" / "trial-2026-10-09" / "connectivity"
    directory.mkdir(parents=True, exist_ok=True)
    if args.attempt < 1:
        parser.error("attempt 必须为正数")
    suffix = "" if args.attempt == 1 else f"_attempt{args.attempt}"
    output = directory / (args.model.replace("/", "_") + suffix + ".json")
    if output.exists():
        parser.error("该模型已有检查记录，拒绝重复付费请求")
    inventory = json.loads((ROOT / "analysis" / "text_inventory.json").read_text(encoding="utf-8"))
    source = inventory[0]["text"]
    key = load_key(ROOT / provider["credential_file"])
    result = check_model(provider, args.model, source, key)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = result["response"]
    choices = data.get("choices", [])
    text = choices[0].get("message", {}).get("content", "") if choices else ""
    print(json.dumps({"model": args.model, "http_status": result["http_status"],
                      "has_translation": bool(text), "usage": data.get("usage"),
                      "error_code": data.get("error", {}).get("code") if isinstance(data.get("error"), dict) else None,
                      "evidence": str(output.relative_to(ROOT))}, ensure_ascii=True))


if __name__ == "__main__":
    main()
