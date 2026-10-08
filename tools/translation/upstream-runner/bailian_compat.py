"""针对百炼修正上游 DeepSeek 原厂参数识别，翻译仍由上游执行。"""

from urllib.parse import urlparse


def uses_bailian_endpoint(api_url: str) -> bool:
    """只接受百炼业务空间主机与官方 DashScope 主机。"""
    host = (urlparse(api_url).hostname or "").lower()
    return host.endswith(".maas.aliyuncs.com") or host in {
        "dashscope.aliyuncs.com",
        "dashscope-intl.aliyuncs.com",
        "dashscope-us.aliyuncs.com",
    }


def install_bailian_compatibility() -> None:
    """百炼使用 extra_body 的 enable_thinking，保留其他渠道原厂行为。"""
    from ModuleFolders.Infrastructure.LLMRequester.OpenaiRequester import OpenaiRequester
    from ModuleFolders.Infrastructure.LLMRequester.AsyncOpenaiRequester import AsyncOpenaiRequester

    for requester_type in (OpenaiRequester, AsyncOpenaiRequester):
        original = requester_type._is_deepseek_request

        def classify(self, platform_config, model_name, fallback=original):
            if uses_bailian_endpoint(platform_config.get("api_url", "")):
                return False
            return fallback(self, platform_config, model_name)

        requester_type._is_deepseek_request = classify
