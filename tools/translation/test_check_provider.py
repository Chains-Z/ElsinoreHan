"""回归验证新版密钥完整读取与诊断脱敏，不接触真实凭证或网络。"""

import tempfile
import unittest
from pathlib import Path

from check_provider import load_key, safe_value


class ProviderCredentialTests(unittest.TestCase):
    def test_segmented_key_is_not_truncated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.txt"
            path.write_text("sk-demo.segment.signature\n", encoding="utf-8")
            self.assertEqual(load_key(path), "sk-demo.segment.signature")

    def test_labeled_key_and_bom_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.txt"
            path.write_text("Key: sk-demo.segment.signature", encoding="utf-8-sig")
            self.assertEqual(load_key(path), "sk-demo.segment.signature")

    def test_multiple_keys_are_rejected_without_echoing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.txt"
            path.write_text("sk-one.segment\nsk-two.segment", encoding="utf-8")
            with self.assertRaises(ValueError) as captured:
                load_key(path)
            self.assertNotIn("sk-one", str(captured.exception))

    def test_error_and_unknown_key_are_redacted(self):
        result = safe_value({"error": "sk-demo.segment.signature sk-other.segment"},
                            "sk-demo.segment.signature")
        self.assertNotIn("sk-", result["error"])
        self.assertNotIn("signature", result["error"])


if __name__ == "__main__":
    unittest.main()
