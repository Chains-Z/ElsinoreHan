"""用离线 HTTPX 传输验证上限、usage、Qwen-MT 协议和密钥脱敏。"""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from request_audit import RequestAudit, RequestLimitExceeded, BudgetLimitExceeded, bridge_qwen_mt


class RequestAuditTests(unittest.TestCase):
    def test_mt_only_sends_numbered_source_and_native_options(self):
        options = {"domains": "Readable game dialogue. Preserve numbered lines.", "terms": [{"source": "Hamlet", "target": "哈姆雷特"}]}
        with patch.dict("os.environ", {"AINIEE_QWEN_TRANSLATION_OPTIONS": json.dumps(options)}):
            body = self.mt_body()
        self.assertEqual(set(body), {"model", "messages", "max_tokens", "stream", "translation_options"})
        self.assertEqual(body["messages"], [{"role": "user", "content": "1.Hello"}])
        self.assertEqual(body["translation_options"], {"source_lang": "English", "target_lang": "Chinese", **options})

    def mt_body(self):
        body = bridge_qwen_mt({"model": "qwen-mt-plus", "max_tokens": 512, "stream": False,
            "enable_thinking": False, "temperature": 1,
            "messages": [{"role": "system", "content": "保留 <textarea> 逐行编号"},
                         {"role": "user", "content": "<textarea>\n1.Hello\n</textarea>"}]})
        return body

    def test_mt_missing_source_duplicate_numbers_and_chinese_domains_rejected(self):
        for source in ("正文", "<textarea>\n1.Hello\n1.World\n</textarea>", "<textarea>\n1.Hello\nExplanation\n</textarea>"):
            with self.assertRaises(RequestLimitExceeded):
                bridge_qwen_mt({"model": "qwen-mt-plus", "max_tokens": 512,
                                "messages": [{"role": "user", "content": source}]})
        with patch.dict("os.environ", {"AINIEE_QWEN_TRANSLATION_OPTIONS": '{"domains":"中文背景"}'}):
            with self.assertRaises(RequestLimitExceeded):
                self.mt_body()

    def test_actual_transport_limit_usage_and_key_redaction(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "audit.jsonl"
            audit = RequestAudit(ledger, max_posts=1, max_output_tokens=512,
                                 prices={"qwen-mt-plus": {"input": 1.0, "output": 1.0}})
            sent = []
            def respond(request):
                sent.append(json.loads(request.content))
                return httpx.Response(200, json={"usage": {"prompt_tokens": 12, "completion_tokens": 8},
                    "choices": [{"message": {"content": "sk-dummy.part-two.segment"}}]})
            original = audit.install()
            try:
                with httpx.Client(transport=httpx.MockTransport(respond)) as client:
                    body = {"model": "qwen-mt-plus", "max_tokens": 512, "messages": [{"role": "system", "content": "规则"},
                            {"role": "user", "content": "<textarea>\n1.Hello\n</textarea>"}], "enable_thinking": False}
                    endpoint = "https://ws-test.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
                    client.post(endpoint, json=body, headers={"Authorization": "Bearer sk-dummy.secret.segments"})
                    with self.assertRaises(RequestLimitExceeded):
                        client.post(endpoint, json=body)
                self.assertEqual(len(sent), 1)
                self.assertEqual(sent[0]["messages"][0]["role"], "user")
                text = ledger.read_text(encoding="utf-8")
                self.assertNotIn("sk-dummy", text)
                self.assertNotIn("Authorization", text)
                completed = json.loads(text.splitlines()[-1])
                self.assertEqual(completed["usage"], {"prompt_tokens": 12, "completion_tokens": 8})
                self.assertTrue(completed["usage_known"])
            finally:
                httpx.Client.send = original

    def test_generic_request_requires_thinking_off_before_transport(self):
        with tempfile.TemporaryDirectory() as temp:
            audit = RequestAudit(Path(temp) / "audit.jsonl")
            original = audit.install()
            try:
                with httpx.Client(transport=httpx.MockTransport(lambda request: self.fail("不应发出请求"))) as client:
                    with self.assertRaises(RequestLimitExceeded):
                        client.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                                    json={"model": "deepseek-pro", "max_tokens": 512})
                self.assertEqual(audit.count, 0)
            finally:
                httpx.Client.send = original

    def test_budget_and_unknown_price_block_before_send(self):
        for prices in ({}, {"deepseek-pro": {"input": 100.0, "output": 100.0}}):
            with tempfile.TemporaryDirectory() as temp:
                audit = RequestAudit(Path(temp) / "audit.jsonl", prices=prices, total_budget_cny=0.01)
                original = audit.install()
                try:
                    with httpx.Client(transport=httpx.MockTransport(lambda request: self.fail("预算失败应不发送"))) as client:
                        with self.assertRaises(BudgetLimitExceeded):
                            client.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                                        json={"model": "deepseek-pro", "max_tokens": 512, "enable_thinking": False})
                    self.assertEqual(audit.count, 0)
                finally:
                    httpx.Client.send = original

    def test_new_process_inherits_request_count_and_releases_known_usage_reserve(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "audit.jsonl"
            prices = {"deepseek-pro": {"input": 100.0, "output": 100.0}}
            audit = RequestAudit(ledger, max_posts=1, prices=prices, total_budget_cny=1.0)
            original = audit.install()
            try:
                with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200,
                        json={"usage": {"prompt_tokens": 12, "completion_tokens": 8}}))) as client:
                    client.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                                json={"model": "deepseek-pro", "max_tokens": 512, "enable_thinking": False})
            finally:
                httpx.Client.send = original
            resumed = RequestAudit(ledger, max_posts=1, prices=prices, total_budget_cny=1.0)
            self.assertEqual(resumed.count, 1)
            self.assertAlmostEqual(resumed.read_accounting()[1], 0.002)
            original = resumed.install()
            try:
                with httpx.Client(transport=httpx.MockTransport(lambda request: self.fail("累计次数应不重置"))) as client:
                    with self.assertRaises(RequestLimitExceeded):
                        client.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                                    json={"model": "deepseek-pro", "max_tokens": 512, "enable_thinking": False})
            finally:
                httpx.Client.send = original

    def test_timeout_keeps_reserve_across_processes(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "audit.jsonl"
            prices = {"deepseek-pro": {"input": 100.0, "output": 100.0}}
            body = {"model": "deepseek-pro", "max_tokens": 512, "enable_thinking": False}
            endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            audit = RequestAudit(ledger, prices=prices, total_budget_cny=0.4)
            original = audit.install()
            def timeout(request):
                raise httpx.ReadTimeout("离线模拟读取超时", request=request)
            try:
                with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
                    with self.assertRaises(httpx.ReadTimeout):
                        client.post(endpoint, json=body)
            finally:
                httpx.Client.send = original
            resumed = RequestAudit(ledger, prices=prices, total_budget_cny=0.4)
            self.assertGreater(resumed.read_accounting()[1], 0.2)
            original = resumed.install()
            try:
                with httpx.Client(transport=httpx.MockTransport(lambda request: self.fail("超时预留不能释放"))) as client:
                    with self.assertRaises(BudgetLimitExceeded):
                        client.post(endpoint, json=body)
            finally:
                httpx.Client.send = original

    def test_glm_mandatory_thinking_low_and_full_reasoning_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "audit.jsonl"
            model = "ZHIPU/GLM-5.3-Flash"
            audit = RequestAudit(ledger, prices={model: {"input": 1.0, "output": 1.0}})
            original = audit.install()
            sent = []
            def respond(request):
                sent.append(json.loads(request.content))
                return httpx.Response(200, json={"usage": {"prompt_tokens": 20, "completion_tokens": 50}})
            endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            try:
                with httpx.Client(transport=httpx.MockTransport(respond)) as client:
                    for fields in ({"enable_thinking": False}, {"enable_thinking": True, "reasoning_effort": "high"}):
                        with self.assertRaises(RequestLimitExceeded):
                            client.post(endpoint, json={"model": model, "max_tokens": 512, **fields})
                    client.post(endpoint, json={"model": model, "max_tokens": 512,
                                              "enable_thinking": True, "reasoning_effort": "low"})
                self.assertEqual(len(sent), 1)
                rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(rows[0]["output_tokens_upper"], 131072 + 512)
                self.assertAlmostEqual(audit.read_accounting()[1], 0.00007)
            finally:
                httpx.Client.send = original


if __name__ == "__main__":
    unittest.main()
