"""在临时游戏目录执行真实安装器，验证不备份且不覆盖原游戏文件。"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GAME = Path("D:/SteamLibrary/steamapps/common/Elsinore")


@unittest.skipUnless(os.name == "nt" and (ROOT / "runtime/build/ElsinoreHan.TranslationToggle.dll").is_file()
                     and (GAME / "Elsinore_Data/Managed").is_dir(), "需要本机已验证的Windows构建依赖")
class NoBackupInstallationTests(unittest.TestCase):
    def test_real_installer_updates_owned_files_without_creating_backup(self):
        evidence = ROOT / "runtime/evidence/full-installed-files.json"
        original_evidence = evidence.read_bytes()
        backup_root = ROOT / "runtime/backups"
        original_backups = sorted(path.name for path in backup_root.iterdir()) if backup_root.exists() else []
        with tempfile.TemporaryDirectory(dir=ROOT / "runtime/build", prefix="install-no-backup-") as directory:
            target = Path(directory)
            originals = ["Elsinore.exe", "UnityPlayer.dll", "Elsinore_Data/resources.assets",
                         "Elsinore_Data/Managed/Assembly-CSharp.dll"]
            for name in originals:
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"original-game-sentinel")
            for source in (GAME / "Elsinore_Data/Managed").glob("Unity*.dll"):
                shutil.copy2(source, target / "Elsinore_Data/Managed" / source.name)
            config = target / "BepInEx/config/AutoTranslatorConfig.ini"
            config.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "runtime/sample/AutoTranslatorConfig.ini", config)
            dictionary = target / "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt"
            dictionary.parent.mkdir(parents=True)
            dictionary.write_text("old-dictionary", encoding="utf-8")
            try:
                result = subprocess.run([shutil.which("pwsh") or "powershell", "-NoProfile", "-NonInteractive",
                                         "-File", str(ROOT / "tools/patch/install-full.ps1"), "-GamePath", directory],
                                        cwd=ROOT, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, (result.stdout + result.stderr).decode(errors="replace"))
                record = json.loads(evidence.read_text(encoding="utf-8-sig"))
                self.assertIsNone(record["backup_path"])
                self.assertEqual(record["backup_policy"], "disabled")
                for name in originals:
                    self.assertEqual((target / name).read_bytes(), b"original-game-sentinel")
                self.assertEqual(len(record["files"]), 8)
                for row in record["files"]:
                    self.assertEqual(hashlib.sha256((target / row["path"]).read_bytes()).hexdigest(), row["sha256"].lower())
                self.assertEqual(sorted(path.name for path in backup_root.iterdir()) if backup_root.exists() else [], original_backups)
            finally:
                evidence.write_bytes(original_evidence)


if __name__ == "__main__":
    unittest.main()
