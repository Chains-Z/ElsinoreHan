"""公开包边界、离线配置及秘密扫描的局部回归。"""

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("public_release_builder", Path(__file__).with_name("build-public-release.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PublicReleaseChecks(unittest.TestCase):
    def test_lf_crlf_and_bom_are_offline(self):
        for separator in ("\n", "\r\n"):
            for encoding in ("utf-8", "utf-8-sig"):
                with self.subTest(separator=repr(separator), encoding=encoding):
                    BUILDER.verify_offline_config(separator.join(("[Service]", "Endpoint=", "FallbackEndpoint=")).encode(encoding))

    def test_active_duplicate_or_missing_endpoint_rejected(self):
        for text in ("Endpoint=Google\nFallbackEndpoint=", "Endpoint=\nFallbackEndpoint=\nEndpoint=Google",
                     "Endpoint=", "Endpoint=\nFallbackEndpoint=\nEndpoint="):
            with self.subTest(text=text), self.assertRaises(ValueError):
                BUILDER.verify_offline_config(text.encode())

    def test_paths_and_player_files_rejected(self):
        for name in ("../game.save", "/tmp/file", "C:/file", "a\\b", "a/./b", "a//b", "",
                     "Elsinore_Data/resources.assets", "Elsinore.exe", "UnityPlayer.dll", ".env",
                     "runtime/backups/checkpoint.json", "game.save", "font.otf", "player.log"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                BUILDER.safe_name(name)
        BUILDER.safe_name("BepInEx/plugins/ElsinoreHan.TranslationToggle.dll")
        BUILDER.safe_name("ElsinoreHan/sources/UnityDoorstop-4.5.0-source.zip")

    def test_exact_local_secret_multiple_encodings_rejected(self):
        secret = "local-test-sensitive-value"
        for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                BUILDER.scan_secret(secret.encode(encoding), "test", [secret])
        BUILDER.scan_secret(b"public content", "test", [secret])


if __name__ == "__main__":
    unittest.main()
