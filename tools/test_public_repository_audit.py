"""验证公开扫描不会把测试目录或已知占位符当成任意密钥的豁免。"""

import unittest

from audit_public_repository import check


class PublicationAuditTests(unittest.TestCase):
    def test_known_placeholder_is_allowed_only_at_its_reviewed_path(self):
        data = b"sk-" + b"demo.segment.signature"
        self.assertEqual(check(data, "tools/translation/test_check_provider.py", []), [])
        self.assertIn("provider_key", check(data, "README.md", []))

    def test_unknown_key_is_rejected_even_in_test_file(self):
        data = b"sk-" + b"z" * 32
        self.assertIn("provider_key", check(data, "tools/translation/test_check_provider.py", []))

    def test_exact_local_secret_is_rejected_in_each_supported_encoding(self):
        secret = "project-secret-for-unit-test"
        for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
            with self.subTest(encoding=encoding):
                self.assertIn("exact_local_secret", check(secret.encode(encoding), "notes.txt", [secret]))

    def test_font_headers_and_private_paths_are_rejected(self):
        self.assertIn("binary_font_archive_or_key", check(b"OTTOdata", "font.bin", []))
        self.assertIn("binary_font_archive_or_key", check(b"data", "font.ttf", []))
        self.assertIn("private_or_local_only_path", check(b"data", "runtime/backups/old.txt", []))
        self.assertIn("personal_save", check(b"data", "game.save", []))


if __name__ == "__main__":
    unittest.main()
