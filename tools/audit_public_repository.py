"""检查公开上传范围及完整Git历史；报告只含路径、规则与哈希，不输出密钥。"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "provider_key": re.compile(rb"\bsk-[A-Za-z0-9._~+/=-]{20,}"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "literal_credential": re.compile(rb'''(?i)["'](?:api[_-]?key|access[_-]?token|client[_-]?secret)["']\s*[:=]\s*["'][A-Za-z0-9_./+-]{24,}["']'''),
}
FORBIDDEN = {".ttf", ".otf", ".ttc", ".woff", ".woff2", ".dll", ".exe", ".zip", ".7z", ".pfx", ".pem", ".key"}
MAGIC = (b"OTTO", b"ttcf", b"wOFF", b"wOF2", b"UnityFS", b"MZ", b"\x00\x01\x00\x00")
TEST_KEYS = {
    "tools/translation/test_check_provider.py": {b"sk-" + b"demo.segment.signature"},
    "tools/translation/upstream-runner/test_request_audit.py": {
        b"sk-" + b"dummy.part-two.segment", b"sk-" + b"dummy.secret.segments"},
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def local_secrets():
    """仅在内存读取本项目已配置密钥，用于精确比对。"""
    secrets = []
    key_path = ROOT / "api-key.txt"
    if key_path.is_file():
        keys = set(re.findall(r"sk-[A-Za-z0-9._~+/=-]+", key_path.read_text(encoding="utf-8-sig")))
        if len(keys) != 1:
            raise ValueError("本地密钥文件须能唯一识别完整Key，禁止跳过精确匹配")
        secrets.extend(keys)
    path = ROOT / ".env"
    if not path.is_file():
        return secrets
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        name, separator, value = line.partition("=")
        if separator and re.search(r"(?:API_KEY|TOKEN|SECRET|PASSWORD)$", name.strip(), re.I):
            value = value.strip().strip("\"'")
            if len(value) >= 12:
                secrets.append(value)
    return secrets


def check(data, path, secrets):
    findings = [name for name, pattern in PATTERNS.items()
                if any(name != "provider_key" or match.group() not in TEST_KEYS.get(path, set())
                       for match in pattern.finditer(data))]
    if any(secret.encode(encoding) in data for secret in secrets for encoding in ("utf-8", "utf-16-le", "utf-16-be")):
        findings.append("exact_local_secret")
    suffix = Path(path).suffix.lower()
    if suffix in FORBIDDEN or data.startswith(MAGIC):
        findings.append("binary_font_archive_or_key")
    if Path(path).name == ".env" or path.startswith(("runtime/vendor/", "runtime/backups/", "runtime/game-test/", "runtime/package/")):
        findings.append("private_or_local_only_path")
    if Path(path).name in ("elsinore_log.json", "game.save", "system.cfg", "system.newcfg"):
        findings.append("personal_save")
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    secrets = local_secrets()
    tracked = [path.decode("utf-8") for path in git("ls-files", "-z").split(b"\0") if path]
    worktree_findings = []
    for path in tracked:
        findings = check((ROOT / path).read_bytes(), path, secrets)
        if findings:
            worktree_findings.append({"path": path, "rules": findings})
    objects = {}
    for line in git("rev-list", "--objects", "--all").decode("utf-8").splitlines():
        oid, _, path = line.partition(" ")
        objects[oid] = path
    metadata = subprocess.check_output(["git", "cat-file", "--batch-check"],
                                       input=("\n".join(objects) + "\n").encode(), cwd=ROOT)
    blobs = [(oid, int(size)) for oid, kind, size in
             (line.split() for line in metadata.decode().splitlines()) if kind == "blob"]
    history_findings = []
    largest = []
    with subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        for oid, size in blobs:
            process.stdin.write((oid + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().split()
            assert header[0].decode() == oid and int(header[2]) == size
            data = process.stdout.read(size)
            assert len(data) == size and process.stdout.read(1) == b"\n"
            findings = check(data, objects[oid], secrets)
            if findings:
                history_findings.append({"object": oid, "path": objects[oid], "rules": findings})
            largest.append({"path": objects[oid], "bytes": size})
        process.stdin.close()
        assert process.wait() == 0
    untracked = [path.decode("utf-8") for path in git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if path]
    untracked_findings = [{"path": path, "rules": rules} for path in untracked
                          if (rules := check((ROOT / path).read_bytes(), path, secrets))]
    ignored = git("check-ignore", ".env", "api-key.txt", "runtime/vendor", "runtime/backups", "runtime/package", "runtime/game-test").decode().splitlines()
    report = {"passed": not (worktree_findings or history_findings or untracked_findings),
              "head": git("rev-parse", "HEAD").decode().strip(),
              "commits": int(git("rev-list", "--count", "HEAD")), "tracked_files": len(tracked),
              "history_blobs": len(blobs), "local_secret_values_compared": len(secrets),
              "worktree_findings": worktree_findings, "history_findings": history_findings,
              "untracked_findings": untracked_findings, "untracked_not_selected_for_upload": untracked,
              "ignored_local_paths": ignored,
              "reviewed_test_placeholders": list(TEST_KEYS),
              "largest_history_blobs": sorted(largest, key=lambda row: row["bytes"], reverse=True)[:5],
              "limits": ["匹配本地密钥及常见凭证格式，不保证识别所有未知密钥格式",
                         "字体及二进制按路径、后缀和文件头检查；文本中的历史字体引用不代表上传字体文件"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "commits", "tracked_files", "history_blobs",
                                                  "local_secret_values_compared", "worktree_findings", "history_findings", "untracked_findings")}))


if __name__ == "__main__":
    main()
