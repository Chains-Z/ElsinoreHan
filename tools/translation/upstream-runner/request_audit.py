"""为上游同步 HTTPX 请求加次数硬闸与实际 usage 账本。"""

from datetime import datetime, timezone
import json
import math
import os
import re
from pathlib import Path
import threading

from bailian_compat import uses_bailian_endpoint
from format_compat import numbered_rows, repair_json_response


class RequestLimitExceeded(RuntimeError):
    """在额外付费 POST 发出之前终止请求。"""


class BudgetLimitExceeded(RequestLimitExceeded):
    """总预算不足时在实际发送前拒绝请求。"""


def redact(value):
    """保留正文调试证据，遮盖常见新版分段 sk- 密钥。"""
    if isinstance(value, str):
        return re.sub(r"sk-[A-Za-z0-9_.-]+", "[REDACTED_API_KEY]", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()
                if key.lower() not in {"authorization", "api_key", "api-key", "headers"}}
    return value


def bridge_qwen_mt(body: dict) -> dict:
    """只取真实源文；领域及术语走官方原生参数，拒绝猜测待译范围。"""
    if not str(body.get("model", "")).lower().startswith("qwen-mt"):
        return body
    users = [message for message in body.get("messages", []) if message.get("role") == "user"]
    blocks = re.findall(r"<textarea>(.*?)</textarea>", str(users[-1].get("content", "")), re.DOTALL) if users else []
    if not blocks or numbered_rows(blocks[-1].strip()) is None:
        raise RequestLimitExceeded("Qwen-MT 请求缺少完整编号的真实源文 textarea，发送前拒绝")
    text = blocks[-1].strip()
    options = json.loads(os.environ.get("AINIEE_QWEN_TRANSLATION_OPTIONS", "{}"))
    options = {"source_lang": "English", "target_lang": "Chinese", **options}
    if set(options) - {"source_lang", "target_lang", "domains", "terms", "tm_list"}:
        raise RequestLimitExceeded("Qwen-MT 存在未知原生翻译参数")
    domains = options.get("domains", "")
    if not isinstance(domains, str) or re.search(r"[\u3400-\u9fff]", domains):
        raise RequestLimitExceeded("Qwen-MT domains 须为官方支持的英文说明")
    return {"model": body["model"], "messages": [{"role": "user", "content": text}],
            "max_tokens": body["max_tokens"], "stream": bool(body.get("stream", False)),
            "translation_options": options}


def disable_sparse_completion() -> None:
    """受限试译关闭自动额外补译；失败交给项目验收标记。"""
    from ModuleFolders.Service.TaskExecutor.TranslatorTask import TranslatorTask

    TranslatorTask.try_sparse_completion = lambda self, response_content, platform_config: (response_content, 0, 0)


def safe_usage(value: dict) -> dict:
    """只记录服务器返回的数值 token 统计，不保存任意响应内容。"""
    result = {}
    keys = {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens",
            "prompt_cache_hit_tokens", "prompt_cache_miss_tokens", "cached_tokens", "reasoning_tokens"}
    for key, item in value.items():
        if key in keys and type(item) is int and item >= 0:
            result[key] = item
        elif key in {"prompt_tokens_details", "completion_tokens_details"} and isinstance(item, dict):
            result[key] = safe_usage(item)
    return result


class RequestAudit:
    """只拦截百炼 chat/completions POST，沿用现成上游翻译调度。"""

    def __init__(self, ledger: Path, max_posts: int = 6, max_output_tokens: int = 4096,
                 prices: dict | None = None, total_budget_cny: float = 4.75):
        if max_posts < 1 or max_output_tokens < 1:
            raise ValueError("请求次数与输出 token 上限必须大于 0")
        self.ledger = ledger
        self.max_posts = max_posts
        self.max_output_tokens = max_output_tokens
        if not math.isfinite(total_budget_cny) or total_budget_cny <= 0:
            raise ValueError("总预算必须是大于 0 的有限金额")
        self.total_budget_cny = total_budget_cny
        self.count = 0
        self.prices = prices or {}
        for rate in self.prices.values():
            if (not isinstance(rate, dict) or any(
                type(rate.get(key)) not in (int, float) or not math.isfinite(rate[key]) or rate[key] < 0
                for key in ("input", "output")
            )):
                raise ValueError("价格配置须包含非负有限 input/output 单价")
        self.lock = threading.Lock()
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.count, _ = self.read_accounting()

    def read_accounting(self) -> tuple[int, float]:
        """跨进程继承计数，已知 usage 替换预留，失败与未完成保持预留。"""
        if not self.ledger.exists():
            return 0, 0.0
        started = {}
        completed = {}
        for line in self.ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            index = row.get("request_index")
            if row.get("event") == "started":
                if index in started:
                    raise ValueError("账本请求编号重复，拒绝继续计费")
                reserved = row.get("reserved_cost_cny")
                if type(reserved) not in (int, float) or not math.isfinite(reserved) or reserved < 0:
                    raise ValueError("账本缺少有效的保守预留费用，拒绝继续计费")
                started[index] = reserved
            elif row.get("event") == "completed" and row.get("usage_known") is True:
                cost = row.get("usage_cost_cny_without_cache_discount")
                if type(cost) in (int, float) and math.isfinite(cost) and cost >= 0:
                    completed[index] = cost
        return len(started), sum(completed.get(index, reserved) for index, reserved in started.items())

    def append(self, event: dict) -> None:
        """先保存发起记录，再保存完成记录；异常网络仍可核对次数。"""
        event = redact({"timestamp": datetime.now(timezone.utc).isoformat(), **event})
        with self.ledger.open("a", encoding="utf-8") as writer:
            writer.write(json.dumps(event, ensure_ascii=False) + "\n")
            writer.flush()
            os.fsync(writer.fileno())

    def install(self):
        """返回原始 send 方法，便于离线测试恢复。"""
        import httpx

        original = httpx.Client.send
        audit = self

        def send(client, request, **kwargs):
            watched = (request.method == "POST" and uses_bailian_endpoint(str(request.url))
                       and request.url.path.endswith("/chat/completions"))
            if not watched:
                return original(client, request, **kwargs)
            body = json.loads(request.content)
            original_body = body
            body = bridge_qwen_mt(body)
            is_qwen_mt = str(body.get("model", "")).lower().startswith("qwen-mt")
            is_glm = str(body.get("model", "")).lower() == "zhipu/glm-5.3-flash"
            if is_glm and not (body.get("enable_thinking") is True and body.get("reasoning_effort") == "low"):
                raise RequestLimitExceeded("GLM-5.3-Flash 小样要求思考开启且 reasoning_effort=low")
            if not is_qwen_mt and not is_glm and body.get("enable_thinking") is not False:
                raise RequestLimitExceeded("小样审计要求关闭思考模式")
            if body is not original_body:
                headers = request.headers.copy()
                headers.pop("content-length", None)
                request = httpx.Request(request.method, request.url, headers=headers,
                                        content=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                        extensions=request.extensions)
            limit = body.get("max_tokens")
            if type(limit) is not int or not 0 < limit <= audit.max_output_tokens:
                raise RequestLimitExceeded("单次输出 token 上限缺失或超出小样额度")
            with audit.lock:
                audit.count, committed = audit.read_accounting()
                if audit.count >= audit.max_posts:
                    raise RequestLimitExceeded("全模型累计请求次数已达上限")
                model = str(body.get("model", ""))
                rate = audit.prices.get(model)
                if rate is None:
                    raise BudgetLimitExceeded("模型没有已核实峰值单价，拒绝发送")
                input_upper = len(request.content) + 2048
                output_upper = limit + (131072 if is_glm else 0)
                reserved = (input_upper * rate["input"] + output_upper * rate["output"]) / 1000000
                if committed + reserved > audit.total_budget_cny:
                    raise BudgetLimitExceeded("累计已用与预留费用加本次上界超过总预算，拒绝发送")
                audit.count += 1
                index = audit.count
                meta = {"request_index": index, "model": model, "max_tokens": limit,
                        "stream": bool(body.get("stream", False)),
                        "input_tokens_upper": input_upper, "output_tokens_upper": output_upper,
                        "reserved_cost_cny": reserved, "estimated_cost_cny": reserved,
                        "committed_before_cny": committed, "total_budget_cny": audit.total_budget_cny,
                        "peak_prices_cny_per_million": rate}
                audit.append({"event": "started", **meta, "request_body": body})
            try:
                response = original(client, request, **kwargs)
                response.read()
                original_response_body = response.text
                usage = {}
                try:
                    payload = response.json()
                    if isinstance(payload, dict) and isinstance(payload.get("usage"), dict):
                        usage = safe_usage(payload["usage"])
                except (ValueError, UnicodeError):
                    for line in response.text.splitlines():
                        if line.startswith("data:"):
                            try:
                                payload = json.loads(line[5:].strip())
                                if isinstance(payload, dict) and isinstance(payload.get("usage"), dict):
                                    usage = safe_usage(payload["usage"])
                            except ValueError:
                                pass
                repaired_response, format_repair = repair_json_response(response, body)
                with audit.lock:
                    cost = None
                    input_usage = usage.get("prompt_tokens", usage.get("input_tokens"))
                    output_usage = usage.get("completion_tokens", usage.get("output_tokens"))
                    if input_usage is not None and output_usage is not None:
                        cost = (input_usage * rate["input"] + output_usage * rate["output"]) / 1000000
                    audit.append({"event": "completed", **meta, "status_code": response.status_code,
                                  "usage": usage, "usage_known": cost is not None,
                                  "usage_cost_cny_without_cache_discount": cost,
                                  "response_body": original_response_body,
                                  "format_repair": format_repair})
                return repaired_response
            except Exception as exc:
                with audit.lock:
                    audit.append({"event": "failed", **meta, "error_type": type(exc).__name__,
                                  "usage_known": False})
                raise

        httpx.Client.send = send
        return original


def install_audit_from_env() -> None:
    """父进程通过非机密环境变量指定独立账本与请求上限。"""
    ledger = os.environ.pop("AINIEE_API_AUDIT_LEDGER", "")
    maximum = int(os.environ.pop("AINIEE_MAX_API_POSTS", "6"))
    output_maximum = int(os.environ.pop("AINIEE_MAX_OUTPUT_TOKENS", "4096"))
    prices = json.loads(os.environ.pop("AINIEE_API_PRICES_JSON", "{}"))
    budget = float(os.environ.pop("AINIEE_TOTAL_BUDGET_CNY", "4.75"))
    if ledger:
        RequestAudit(Path(ledger), maximum, output_maximum, prices, budget).install()
        disable_sparse_completion()
