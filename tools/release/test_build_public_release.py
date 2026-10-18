"""公开包边界、离线配置及秘密扫描的局部回归。"""

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("public_release_builder", Path(__file__).with_name("build-public-release.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PublicReleaseChecks(unittest.TestCase):
    PLUGIN_SOURCE = '[BepInPlugin("elsinorehan.translationtoggle", "ElsinoreHan Translation Toggle", "1.5.15")]'

    def source_fixture(self):
        sources = {name: ("测试源码：" + name).encode("utf-8") for name in BUILDER.PLUGIN_SOURCES}
        script = (Path(__file__).parent.parent / "patch/build-toggle.ps1").read_text(encoding="utf-8-sig")
        hashes = ["b" * 64] + [BUILDER.digest(sources[name]) for name in BUILDER.PLUGIN_SOURCES] + ["c" * 64] * 10
        return sources, script, {"input_fingerprint": ":".join(hashes), "output_sha256": "a" * 64}

    def test_complete_sources_match_original_build_record(self):
        sources, script, record = self.source_fixture()
        BUILDER.verify_plugin_sources(sources, script, record, "a" * 64)

    def test_missing_changed_or_unrelated_binary_sources_rejected(self):
        sources, script, record = self.source_fixture()
        for invalid_sources, plugin_hash in (({k: v for k, v in sources.items() if k != "CreditsHoldSkip.cs"}, "a" * 64),
                                             ({**sources, "CreditsHoldSkip.cs": b"changed"}, "a" * 64),
                                             (sources, "d" * 64)):
            with self.subTest(plugin_hash=plugin_hash), self.assertRaises(ValueError):
                BUILDER.verify_plugin_sources(invalid_sources, script, record, plugin_hash)

    def test_new_build_source_cannot_be_omitted_from_archive(self):
        sources, script, record = self.source_fixture()
        changed_script = script + "\n$newSource = Join-Path $PSScriptRoot 'NewFeature.cs'\n"
        with self.assertRaises(ValueError):
            BUILDER.verify_plugin_sources(sources, changed_script, record, "a" * 64)

    def test_player_documents_are_readable_without_markdown_viewer(self):
        data = BUILDER.player_document('# 使用说明\n\n按 **Ctrl** 跳过，详见 [安装方法](INSTALL.md)。\n[项目仓库](https://github.com/Chains-Z/ElsinoreHan)\n> 补丁版本：`1.0.0`\n')
        self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        text = data.decode('utf-8-sig')
        self.assertIn('安装方法（安装方法.txt）', text)
        self.assertIn('项目仓库（https://github.com/Chains-Z/ElsinoreHan）', text)
        self.assertIn('按 Ctrl 跳过', text)
        self.assertNotIn('**', text)
        self.assertNotIn('\n', text.replace('\r\n', ''))
        self.assertEqual(len(set(BUILDER.DOCS.values())), 4)
        self.assertTrue(all('/' not in name and name.endswith('.txt') for name in BUILDER.DOCS.values()))

    def test_public_version_changes_independently(self):
        for public_version in ("1.0.0", "1.0.1", "2.0.0"):
            result = BUILDER.verify_versions({"patch_version": public_version, "internal_version": "1.5.15"}, "1.5.15", self.PLUGIN_SOURCE)
            self.assertEqual(result["release_id"], "v" + public_version)
            self.assertEqual(result["internal_version"], "1.5.15")

    def test_invalid_or_missing_versions_rejected(self):
        for invalid in ("v1.0.0", "01.0.0", "1.0", "1.0.0\n", "1.0.0-zh", None, 1):
            for field in ("patch_version", "internal_version"):
                metadata = {"patch_version": "1.0.0", "internal_version": "1.5.15", field: invalid}
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    BUILDER.verify_versions(metadata, "1.5.15", self.PLUGIN_SOURCE)
        with self.assertRaises(ValueError):
            BUILDER.verify_versions({"patch_version": "1.0.0"}, "1.5.15", self.PLUGIN_SOURCE)

    def test_internal_version_requires_installed_and_declared_agreement(self):
        metadata = {"patch_version": "1.0.0", "internal_version": "1.5.15"}
        for installed, source in (("1.5.14", self.PLUGIN_SOURCE), ("1.5.15", ""),
                                  ("1.5.15", self.PLUGIN_SOURCE.replace("1.5.15", "1.5.14"))):
            with self.subTest(installed=installed, source=source), self.assertRaises(ValueError):
                BUILDER.verify_versions(metadata, installed, source)

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
