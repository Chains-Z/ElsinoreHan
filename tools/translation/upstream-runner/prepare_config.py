"""将不含密钥的任务配置安装到被忽略的上游运行目录。"""

import argparse
import copy
import json
from pathlib import Path


def write_json(path: Path, value: dict) -> None:
    """以 UTF-8 保存上游配置。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="配置现成 AiNiee-Next，不接收 API Key")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--thinking", choices=("true", "false"), default="false")
    parser.add_argument("--prompt", type=Path, help="系统提示词；省略则使用上游基础提示")
    parser.add_argument("--style", type=Path, help="中文文风说明")
    parser.add_argument("--rules", type=Path, help="角色与术语等规则 profile 的 JSON")
    parser.add_argument("--profile", default="elsinore-pilot")
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    args = parser.parse_args()
    if not args.profile or any(char in args.profile for char in '/\\:*?"<>|'):
        parser.error("profile 必须是普通文件名")
    root = Path(__file__).resolve().parents[3]
    resource = root / "runtime/vendor/AiNiee-Next/Resource"
    prompt_path = args.prompt or resource / "Prompt/Translate/common_system_zh.txt"
    platform = {
        "tag": "custom", "group": "custom", "name": "百炼小样", "api_format": "OpenAI",
        "api_url": args.base_url, "api_key": "", "model": args.model,
        "auto_complete": True, "rpm_limit": 6, "tpm_limit": 30000,
        "temperature": 1.0, "top_p": 1.0, "presence_penalty": 0.0,
        "frequency_penalty": 0.0, "think_switch": False,
        "extra_body": {"enable_thinking": args.thinking == "true"},
        "max_output_tokens": args.max_output_tokens,
    }
    if args.model.lower() == "zhipu/glm-5.3-flash" and args.thinking == "true":
        platform["extra_body"]["reasoning_effort"] = "low"
    profile = {
        "translation_execution_mode": "default_api", "external_agent_onboarding": False,
        "external_agent_onboarding_status": "accepted", "source_language": "english",
        "target_language": "chinese_simplified", "translation_project": "Vnt",
        "target_platform": "custom", "base_url": args.base_url, "model": args.model,
        "api_key": "", "api_settings": {"translate": "custom", "polish": "custom"},
        "platforms": {"custom": platform}, "sdk_request_mode": "httpx",
        "enable_stream_api": False, "enable_prompt_caching": False,
        "enable_async_mode": False, "translation_consistency_enhancement": False,
        "response_conversion_toggle": False, "opencc_preset": "t2s.json",
        "user_thread_counts": 1, "retry_count": 0, "round_limit": 1,
        "lines_limit": 15, "chunk_soft_limit_extra_lines": 0, "tokens_limit_switch": False,
        "pre_line_counts": 0, "request_timeout": 90, "enable_api_failover": False,
        "enable_smart_round_limit": False, "enable_task_notification": False,
        "enable_background_prewarm": False, "enable_github_promotion": False,
        "enable_auto_restore_ebook": False, "enable_batch_auto_merge_ebook": False,
        "enable_bilingual_output": False, "enable_session_logging": True,
        "translation_prompt_selection": {
            "last_selected_id": 999999,
            "prompt_content": prompt_path.read_text(encoding="utf-8-sig"),
        },
        "response_check_switch": {
            "newline_character_count_check": True, "return_to_original_text_check": False,
            "residual_original_text_check": False, "reply_format_check": True,
            "untranslated_retry_limit": 0,
        },
    }
    rules = {
        "prompt_dictionary_switch": False, "prompt_dictionary_data": [],
        "characterization_switch": False, "characterization_data": [],
        "character_recall_switch": False, "world_building_switch": False,
        "world_building_content": "", "writing_style_switch": bool(args.style),
        "writing_style_content": args.style.read_text(encoding="utf-8-sig") if args.style else "",
        "translation_example_switch": False, "translation_example_data": [],
        "dynamic_glossary_switch": False, "translation_memory_switch": False,
        "pre_translation_switch": False, "post_translation_switch": False,
        "exclusion_list_switch": False,
    }
    if args.rules:
        rules.update(json.loads(args.rules.read_text(encoding="utf-8-sig")))
    write_json(resource / "profiles" / f"{args.profile}.json", profile)
    write_json(resource / "rules_profiles" / f"{args.profile}.json", rules)
    root_path = resource / "config.json"
    root_config = json.loads(root_path.read_text(encoding="utf-8-sig")) if root_path.exists() else {}
    root_config = copy.deepcopy(root_config)
    root_config.update({"wizard_completed": True, "active_profile": args.profile,
                        "active_rules_profile": args.profile})
    write_json(root_path, root_config)
    print(f"已准备不含密钥的 profile：{args.profile}；尚未调用模型。")


if __name__ == "__main__":
    main()
