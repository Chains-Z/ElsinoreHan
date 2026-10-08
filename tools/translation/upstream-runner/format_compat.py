"""只给编号完整的裸译文增加 textarea 包装，不改任何译句。"""

import copy
import json
import re


def numbered_rows(content: str) -> list[int] | None:
    """每行必须有唯一顺序编号和非空正文，拒绝说明、围栏或多行混合。"""
    rows = content.splitlines()
    if not rows:
        return None
    numbers = []
    for row in rows:
        match = re.fullmatch(r"([1-9]\d*)\.(.+)", row)
        if not match or not match.group(2).strip():
            return None
        text = re.sub(r"^(?:\[[^\]\r\n]+\])+", "", match.group(2).strip()).strip()
        if not text:
            return None
        numbers.append(int(match.group(1)))
    if len(set(numbers)) != len(numbers) or numbers != sorted(numbers):
        return None
    return numbers


def wrap_complete_numbered_translation(content: str, request_body: dict) -> tuple[str, dict | None]:
    """匹配最后源文 textarea，避免把 Qwen 单 user 中的系统示例当源文。"""
    if not isinstance(content, str) or "<textarea" in content or "</textarea>" in content:
        return content, None
    prompt = "\n\n".join(str(message.get("content", "")) for message in request_body.get("messages", []))
    source_blocks = re.findall(r"<textarea>(.*?)</textarea>", prompt, re.DOTALL)
    if source_blocks:
        expected = numbered_rows(source_blocks[-1].strip())
    elif str(request_body.get("model", "")).lower().startswith("qwen-mt") and request_body.get("translation_options"):
        expected = numbered_rows(prompt.strip())
    else:
        return content, None
    actual = numbered_rows(content)
    if expected is None or actual != expected:
        return content, None
    return "<textarea>\n" + content + "\n</textarea>", {
        "kind": "textarea_wrapper_only", "matched_numbers": actual,
    }


def repair_json_response(response, request_body: dict):
    """原 response 不变；验证成功后返回仅包裹 content 的新响应与审计说明。"""
    import httpx

    if response.status_code != 200:
        return response, None
    try:
        payload = response.json()
    except ValueError:
        return response, None
    if not isinstance(payload, dict):
        return response, None
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return response, None
    if choices[0].get("finish_reason") in {"length", "content_filter"}:
        return response, None
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        return response, None
    repaired, note = wrap_complete_numbered_translation(message["content"], request_body)
    if note is None:
        return response, None
    patched = copy.deepcopy(payload)
    patched["choices"][0]["message"]["content"] = repaired
    headers = response.headers.copy()
    for key in ("content-length", "content-encoding", "transfer-encoding"):
        headers.pop(key, None)
    return httpx.Response(response.status_code, headers=headers,
                          content=json.dumps(patched, ensure_ascii=False).encode("utf-8"),
                          request=response.request, extensions=response.extensions), note
