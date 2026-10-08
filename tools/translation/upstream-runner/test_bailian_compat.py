"""核实百炼兼容分支的主机边界，避免误改其他平台。"""

import unittest
from pathlib import Path
import sys

from bailian_compat import install_bailian_compatibility, uses_bailian_endpoint


class BailianHostTests(unittest.TestCase):
    def test_workspace_and_official_hosts(self):
        for endpoint in (
            "https://ws-example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ):
            self.assertTrue(uses_bailian_endpoint(endpoint))

    def test_other_providers_and_deceptive_hosts(self):
        for endpoint in (
            "https://api.deepseek.com/v1",
            "https://notmaas.aliyuncs.com/v1",
            "https://dashscope.aliyuncs.com.attacker.example/v1",
            "https://example.com/?q=maas.aliyuncs.com",
        ):
            self.assertFalse(uses_bailian_endpoint(endpoint))

    def test_both_upstream_requesters_select_bailian_parameters(self):
        upstream = Path(__file__).resolve().parents[3] / "runtime/vendor/AiNiee-Next"
        sys.path.insert(0, str(upstream))
        from ModuleFolders.Infrastructure.LLMRequester.OpenaiRequester import OpenaiRequester
        from ModuleFolders.Infrastructure.LLMRequester.AsyncOpenaiRequester import AsyncOpenaiRequester
        original_methods = {kind: kind._is_deepseek_request for kind in (OpenaiRequester, AsyncOpenaiRequester)}
        try:
            install_bailian_compatibility()
            for kind in original_methods:
                requester = object.__new__(kind)
                self.assertFalse(requester._is_deepseek_request(
                    {"api_url": "https://ws-test.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"},
                    "deepseek-v4-pro",
                ))
                self.assertTrue(requester._is_deepseek_request(
                    {"api_url": "https://api.deepseek.com/v1"}, "deepseek-v4-pro",
                ))
        finally:
            for kind, method in original_methods.items():
                kind._is_deepseek_request = method


if __name__ == "__main__":
    unittest.main()
