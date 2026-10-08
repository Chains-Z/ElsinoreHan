"""离线执行完整传统 API 批译入口，防止零轮配置空跑被视为通过。"""

import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


def run_child(temp: Path, frozen_flash: bool = False, qwen_native: bool = False) -> None:
    """真实 Reader/Executor/Writer 配合本地 HTTPX 响应，无真实模型费用。"""
    import httpx
    import prepare_config
    from launch import configure_non_interactive_translation

    root = Path(__file__).resolve().parents[3]
    upstream = root / "runtime/vendor/AiNiee-Next"
    sys.path.insert(0, str(upstream))
    module = importlib.import_module("ainiee_cli")
    from ModuleFolders.Base.Base import Base
    from ModuleFolders.Infrastructure.TaskConfig.ConfigProfileService import deep_merge, load_master_preset
    from request_audit import disable_sparse_completion, RequestAudit

    resource = temp / "runtime/vendor/AiNiee-Next/Resource"
    prompt = resource / "Prompt/Translate/common_system_zh.txt"
    prompt.parent.mkdir(parents=True)
    prompt.write_text((upstream / "Resource/Prompt/Translate/common_system_zh.txt").read_text(encoding="utf-8"), encoding="utf-8")
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model = "qwen-mt-plus" if qwen_native else "offline-test-model"
    with patch.object(prepare_config, "__file__", str(temp / "tools/translation/upstream-runner/prepare_config.py")), \
         patch.object(sys, "argv", ["prepare_config.py", "--base-url", base_url, "--model", model]):
        prepare_config.main()
    config = deep_merge(load_master_preset(), json.loads((resource / "profiles/elsinore-pilot.json").read_text(encoding="utf-8")))
    config.update(json.loads((resource / "rules_profiles/elsinore-pilot.json").read_text(encoding="utf-8")))
    config["enable_session_logging"] = False
    config["enable_task_notification"] = False

    if frozen_flash:
        entries = json.loads((root / "translation/trial-2026-10-09/inputs/01_hamlet_ghost_followup.json").read_text(encoding="utf-8"))
        frozen = json.loads((Path(__file__).parent / "fixtures/flash-numbered-response.json").read_text(encoding="utf-8"))["response_bodies"]
    else:
        entries = json.loads((root / "translation/pilot/input/dialogue/Spine_OpheliaHamletStarter.json").read_text(encoding="utf-8"))[:2]
    source = temp / "integration-input.json"
    source.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    output = temp / "output"
    requests = []
    def respond(client, request, **kwargs):
        body = json.loads(request.content)
        requests.append(body)
        if frozen_flash:
            return httpx.Response(200, request=request, content=frozen[len(requests) - 1].encode("utf-8"),
                                  headers={"content-type": "application/json"})
        content = "1.[Ophelia]怎么回事？\n2.[Ophelia]你白天也能现身？"
        return httpx.Response(200, request=request, json={
            "choices": [{"message": {"content": content if qwen_native else "<textarea>\n" + content + "\n</textarea>"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 25},
        })
    def load_config(cli, *args, **kwargs):
        cli.config = copy.deepcopy(config)
        cli.root_config = {}
        cli.active_profile_name = "elsinore-pilot"
        cli.active_rules_profile_name = "elsinore-pilot"

    argv = [str(upstream / "ainiee_cli.py"), "translate", str(source), "--type", "Vnt",
            "--output", str(output), "--yes", "--web-mode", "--rounds", "1", "--retry", "0", "--threads", "1"]
    configure_non_interactive_translation(module, argv[1:])
    disable_sparse_completion()
    os.chdir(upstream)
    with patch.object(sys, "argv", argv), \
         patch.object(module.CLIMenu, "load_config", load_config), \
         patch.object(module.CLIMenu, "save_config", lambda self, **kwargs: None), \
         patch.object(Base, "load_config", lambda self: copy.deepcopy(config)), \
         patch.object(Base, "save_config", lambda self, value: None), \
         patch("httpx.Client.send", respond), \
         patch("requests.sessions.Session.request", side_effect=AssertionError("测试禁止外部网络")), \
         patch("urllib.request.urlopen", side_effect=AssertionError("测试禁止外部下载")), \
         patch("rich.prompt.Prompt.ask", side_effect=AssertionError("测试禁止交互")), \
         patch("rich.prompt.IntPrompt.ask", side_effect=AssertionError("测试禁止交互")):
        if frozen_flash or qwen_native:
            if qwen_native:
                os.environ["AINIEE_QWEN_TRANSLATION_OPTIONS"] = json.dumps({"domains": "Readable game dialogue; preserve numbered entries.",
                                                                        "terms": [{"source": "Ophelia", "target": "奥菲莉娅"}]})
            RequestAudit(temp / "frozen-audit.jsonl", max_posts=2,
                         prices={model: {"input": 1.0, "output": 1.0}}).install()
        try:
            module.main()
        except SystemExit as exc:
            exit_code = exc.code
        else:
            exit_code = 0
    if exit_code != 0:
        raise AssertionError(f"CLI 返回非零：{exit_code}")
    expected_requests = 2 if frozen_flash else 1
    if len(requests) != expected_requests:
        raise AssertionError(f"首轮应有 {expected_requests} 次 HTTP 请求，实际：{len(requests)}")
    results = [file for file in output.rglob("*.json") if file.name == source.name]
    if len(results) != 1:
        raise AssertionError(f"未得到唯一 Vnt 输出：{results}")
    translated = json.loads(results[0].read_text(encoding="utf-8"))
    if len(translated) != len(entries) or not all(any("\u4e00" <= char <= "\u9fff" for char in item["message"]) for item in translated):
        raise AssertionError("输出必须完整保留行数且各条有中文正文，不能沿用原文假通过")
    if not frozen_flash and (translated[0]["message"] != "怎么回事？" or translated[1]["message"] != "你白天也能现身？"):
        raise AssertionError("简体假响应不得被上游继承的 s2twp 配置转成繁体")
    if config["response_conversion_toggle"] is not False:
        raise AssertionError("必须显式覆盖上游 preset 的自动转繁体默认值")
    if requests[0].get("max_tokens") != 4096:
        raise AssertionError("输出上限没有进入真实 HTTP 请求体")
    if frozen_flash:
        completed = [json.loads(line) for line in (temp / "frozen-audit.jsonl").read_text(encoding="utf-8").splitlines()
                     if json.loads(line)["event"] == "completed"]
        if [row["response_body"] for row in completed] != frozen:
            raise AssertionError("审计必须原样保留已付费真实响应，不写修复后的正文")
        if not all(row["format_repair"]["kind"] == "textarea_wrapper_only" for row in completed):
            raise AssertionError("两批完整编号响应应只补 wrapper")
    if qwen_native:
        sent = requests[0]
        expected_source = "\n".join(str(index + 1) + ".[" + item["name"] + "]" + item["message"] for index, item in enumerate(entries))
        if sent["messages"] != [{"role": "user", "content": expected_source}]:
            raise AssertionError("Qwen 只应收到逐行真实源文，不发送系统说明和背景供翻译")
        if sent["translation_options"]["terms"] != [{"source": "Ophelia", "target": "奥菲莉娅"}]:
            raise AssertionError("术语未进入官方原生参数")
        completed = json.loads((temp / "frozen-audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        if "<textarea>" in json.loads(completed["response_body"])["choices"][0]["message"]["content"]:
            raise AssertionError("冻结响应不得被包装修复覆盖")
        if completed["format_repair"]["kind"] != "textarea_wrapper_only":
            raise AssertionError("只有完整编号响应能补回工具所需包装")
    (temp / "probe-result.json").write_text(json.dumps({"http_requests": len(requests), "output_rows": len(translated),
                                                        "round_limit": config["round_limit"]}), encoding="utf-8")


class ExecutorIntegrationTests(unittest.TestCase):
    def check_child(self, frozen_flash=False, qwen_native=False):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.pop("AINIEE_WEB_TASK_API_KEY", None)
            env["PYTHONUTF8"] = "1"
            flag = "--integration-child-qwen" if qwen_native else "--integration-child-frozen" if frozen_flash else "--integration-child"
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), flag, temp],
                                    capture_output=True, text=True, encoding="utf-8", env=env, timeout=40,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.assertEqual(result.returncode, 0, result.stdout[-6000:] + result.stderr[-3000:])
            self.assertEqual(json.loads((Path(temp) / "probe-result.json").read_text(encoding="utf-8")),
                             {"http_requests": 2 if frozen_flash else 1, "output_rows": 20 if frozen_flash else 2, "round_limit": 1})

    def test_legal_single_round_reaches_http_and_writes_chinese(self):
        self.check_child()

    def test_frozen_flash_response_reaches_writer_without_extra_request(self):
        self.check_child(frozen_flash=True)

    def test_native_qwen_source_and_terms_reach_writer_with_reversible_wrapper(self):
        self.check_child(qwen_native=True)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] in {"--integration-child", "--integration-child-frozen", "--integration-child-qwen"}:
        run_child(Path(sys.argv[2]), frozen_flash=sys.argv[1] == "--integration-child-frozen", qwen_native=sys.argv[1] == "--integration-child-qwen")
    else:
        unittest.main()
