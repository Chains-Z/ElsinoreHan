"""归档恢复器的错误输入及保守写入回归。"""

import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


SPEC = importlib.util.spec_from_file_location("restore_workspace", Path(__file__).with_name("restore-release-workspace.py"))
RESTORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESTORE)


class RecoveryChecks(unittest.TestCase):
    def test_wrong_archive_hash_and_unlisted_entry_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "package.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("unexpected", b"data")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                RESTORE.checked_archive(path, "0" * 64, {})
            with self.assertRaisesRegex(ValueError, "额外"):
                RESTORE.checked_archive(path, RESTORE.digest(path.read_bytes()), {})

    def test_entry_hash_rejected_even_when_archive_hash_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "package.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("file", b"data")
            with self.assertRaisesRegex(ValueError, "条目"):
                RESTORE.checked_archive(path, RESTORE.digest(path.read_bytes()),
                                        {"file": {"size": 4, "sha256": "0" * 64}})

    def test_conflict_preflight_leaves_all_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runtime").mkdir()
            old = root / "runtime/existing"
            old.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "拒绝覆盖"):
                RESTORE.write_missing(root, {"runtime/new": b"new", "runtime/existing": b"baseline"})
            self.assertFalse((root / "runtime/new").exists())
            self.assertEqual(old.read_bytes(), b"modified")

    def test_escape_rejected_and_identical_restore_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ("README.md", "runtime/../escaped", "runtime/../../outside"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    RESTORE.write_missing(root, {path: b"unsafe"})
            self.assertEqual(RESTORE.write_missing(root, {"runtime/file": b"same"}), 1)
            self.assertEqual(RESTORE.write_missing(root, {"runtime/file": b"same"}), 0)


if __name__ == "__main__":
    unittest.main()
