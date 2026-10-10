"""用真实独占文件验证并行游玩时不读取实时日志；不启动游戏。"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == "nt", "需要Windows文件独占语义")
class SaveSnapshotTests(unittest.TestCase):
    def run_script(self, script):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "check.ps1"
            helper = str(Path(__file__).with_name("ProbeSaveSnapshot.ps1")).replace("'", "''")
            path.write_text("$ErrorActionPreference='Stop'\n. '" + helper + "'\n" + script,
                            encoding="utf-8-sig")
            result = subprocess.run([shutil.which("pwsh"), "-NoProfile", "-File", str(path)],
                                    capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr).decode("utf-8", "replace"))

    def test_concurrent_game_skips_exclusively_locked_live_log(self):
        self.run_script("""
$testRoot = Join-Path $PSScriptRoot 'save'
New-Item -ItemType Directory -Path $testRoot | Out-Null
$log = Join-Path $testRoot 'elsinore_log.json'
[IO.File]::WriteAllText($log, 'real lock test')
$stream = [IO.File]::Open($log, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
try {
    $snapshot = @(Get-ProbeSaveSnapshot -Path $testRoot -ConcurrentGameActive $true)
    if ($snapshot.Count -ne 0) { throw '并行游玩时不应读取实时文件' }
    $rejected = $false
    try { $null = @(Get-ProbeSaveSnapshot -Path $testRoot -ConcurrentGameActive $false) }
    catch { $rejected = $true }
    if (-not $rejected) { throw '对照未复现真实独占文件读取失败' }
} finally { $stream.Dispose() }
""")

    def test_closed_game_records_hash_and_time_for_every_file(self):
        self.run_script("""
$testRoot = Join-Path $PSScriptRoot 'save'
New-Item -ItemType Directory -Path $testRoot | Out-Null
$save = Join-Path $testRoot 'game.save'
[IO.File]::WriteAllText($save, 'snapshot test')
$snapshot = @(Get-ProbeSaveSnapshot -Path $testRoot -ConcurrentGameActive $false)
if ($snapshot.Count -ne 1 -or $snapshot[0].path -ne 'game.save' -or $snapshot[0].sha256 -ne (Get-FileHash -LiteralPath $save).Hash -or $snapshot[0].write_time -ne (Get-Item -LiteralPath $save).LastWriteTimeUtc.ToString('o')) { throw '静止存档快照不完整' }
""")


if __name__ == "__main__":
    unittest.main()
