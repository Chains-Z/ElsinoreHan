"""调用固定版本 AiNiee-Next CLI，不读取或持久保存密钥。"""

from pathlib import Path
import importlib
import os
import sys

from bailian_compat import install_bailian_compatibility
from request_audit import install_audit_from_env


def configure_non_interactive_translation(module, arguments: list[str]) -> bool:
    """传统 API 非交互翻译跳过无关 WebUI 安装提示，保留队列初始状态。"""
    if "translate" not in arguments or not any(flag in arguments for flag in ("--yes", "-y")):
        return False
    if "--manga" in arguments:
        return False

    def initialize_queue_state(self):
        self._last_queue_log_size = 0
        self._queue_log_monitor_thread = None
        self._queue_log_monitor_running = False

    module.CLIMenu._check_web_server_dist = initialize_queue_state
    return True


def absolutize_translation_paths(arguments: list[str], caller_directory: Path) -> list[str]:
    """切换上游工作目录前，将常用翻译输入输出路径转为绝对路径。"""
    result = list(arguments)
    path_flags = {"--output", "-o", "--queue-file", "--workflow-file"}
    for index, argument in enumerate(arguments):
        if argument in path_flags and index + 1 < len(result):
            path = Path(result[index + 1]).expanduser()
            result[index + 1] = str(path if path.is_absolute() else (caller_directory / path).resolve())
    if "translate" in arguments:
        index = arguments.index("translate") + 1
        if index < len(result) and not result[index].startswith("-"):
            path = Path(result[index]).expanduser()
            result[index] = str(path if path.is_absolute() else (caller_directory / path).resolve())
    return result


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    upstream = project_root / "runtime/vendor/AiNiee-Next"
    entry = upstream / "ainiee_cli.py"
    if not entry.is_file():
        raise SystemExit("缺少固定版本 AiNiee-Next，见 runner-setup.md。")
    sys.path.insert(0, str(upstream))
    install_audit_from_env()
    install_bailian_compatibility()
    sys.argv[1:] = absolutize_translation_paths(sys.argv[1:], Path.cwd())
    os.chdir(upstream)
    sys.argv[0] = str(entry)
    module = importlib.import_module("ainiee_cli")
    configure_non_interactive_translation(module, sys.argv[1:])
    module.main()


if __name__ == "__main__":
    main()
