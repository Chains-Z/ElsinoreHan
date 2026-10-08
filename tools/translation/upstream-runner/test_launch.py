"""离线核实真实非交互初始化可进入 VNText Reader 与翻译执行器。"""

import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from launch import configure_non_interactive_translation, absolutize_translation_paths


class NonInteractiveLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(cls.root / "runtime/vendor/AiNiee-Next"))
        cls.module = importlib.import_module("ainiee_cli")

    def test_patch_is_scoped_to_non_interactive_translate(self):
        original = self.module.CLIMenu._check_web_server_dist
        try:
            self.assertFalse(configure_non_interactive_translation(self.module, ["translate", "input.json"]))
            self.assertFalse(configure_non_interactive_translation(self.module, ["polish", "input.json", "--yes"]))
            self.assertIs(self.module.CLIMenu._check_web_server_dist, original)
        finally:
            self.module.CLIMenu._check_web_server_dist = original

    def test_relative_input_and_output_survive_upstream_cwd(self):
        result = absolutize_translation_paths(["translate", "samples/source.json", "--output", "out", "--yes"], self.root)
        self.assertEqual(Path(result[1]), self.root / "samples/source.json")
        self.assertEqual(Path(result[3]), self.root / "out")

    def test_real_reader_and_executor_initialize_without_web_prompt_or_network(self):
        original = self.module.CLIMenu._check_web_server_dist
        try:
            configure_non_interactive_translation(self.module, ["translate", "input.json", "--yes"])
            with patch("rich.prompt.IntPrompt.ask", side_effect=AssertionError("不得要求安装 WebUI")), \
                 patch("rich.prompt.Prompt.ask", side_effect=AssertionError("不得进入交互提示")), \
                 patch("requests.sessions.Session.request", side_effect=AssertionError("离线测试不得联网")), \
                 patch("httpx.Client.send", side_effect=AssertionError("离线测试不得发送 API")), \
                 patch("urllib.request.urlopen", side_effect=AssertionError("离线测试不得下载资源")):
                cli = self.module.CLIMenu()
                self.assertIsNone(cli._update_manager)
                self.assertIsNone(cli._queue_log_monitor_thread)
                reader = cli.file_reader
                executor = cli.task_executor
                sample = self.root / "translation/pilot/input/dialogue/Spine_OpheliaHamletStarter.json"
                entry = json.loads(sample.read_text(encoding="utf-8-sig"))[0]
                with tempfile.TemporaryDirectory() as temp:
                    source = Path(temp) / "reader-smoke.json"
                    source.write_text(json.dumps([entry], ensure_ascii=False), encoding="utf-8")
                    cache = reader.read_files("Vnt", str(source), "")
                    self.assertEqual(len(cache.files), 1)
                    file_data = next(iter(cache.files.values()))
                    self.assertEqual(len(file_data.items), 1)
                    self.assertIn(entry["message"], file_data.items[0].source_text)
                self.assertIs(executor.file_reader, reader)
                self.assertIs(executor.cache_manager, cli.cache_manager)
        finally:
            self.module.CLIMenu._check_web_server_dist = original


if __name__ == "__main__":
    unittest.main()
