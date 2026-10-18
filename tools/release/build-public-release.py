"""按固定白名单制作平铺公开包，并核对来源、许可、对应源码和敏感信息。"""

from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from audit_public_repository import PATTERNS, local_secrets
sys.path.insert(0, str(ROOT / "tools/translation"))
from export_sol_full import encode

PAYLOAD = (
    ".doorstop_version", "changelog.txt", "doorstop_config.ini", "elsinorehan_sans_sdf_u2018",
    "winhttp.dll", "XUnity-LICENSE", "BepInEx/config/AutoTranslatorConfig.ini",
    "BepInEx/core/0Harmony.dll", "BepInEx/core/0Harmony.xml", "BepInEx/core/0Harmony20.dll",
    "BepInEx/core/BepInEx.dll", "BepInEx/core/BepInEx.Harmony.dll", "BepInEx/core/BepInEx.Harmony.xml",
    "BepInEx/core/BepInEx.Preloader.dll", "BepInEx/core/BepInEx.Preloader.xml", "BepInEx/core/BepInEx.xml",
    "BepInEx/core/HarmonyXInterop.dll", "BepInEx/core/Mono.Cecil.dll", "BepInEx/core/Mono.Cecil.Mdb.dll",
    "BepInEx/core/Mono.Cecil.Pdb.dll", "BepInEx/core/Mono.Cecil.Rocks.dll",
    "BepInEx/core/MonoMod.RuntimeDetour.dll", "BepInEx/core/MonoMod.RuntimeDetour.xml",
    "BepInEx/core/MonoMod.Utils.dll", "BepInEx/core/MonoMod.Utils.xml", "BepInEx/core/XUnity.Common.dll",
    "BepInEx/plugins/ElsinoreHan.TranslationToggle.dll", "BepInEx/plugins/README (AutoTranslator).md",
    "BepInEx/plugins/XUnity.AutoTranslator/ExIni.dll",
    "BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.BepInEx.dll",
    "BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll",
    "BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.ExtProtocol.dll",
    "BepInEx/plugins/XUnity.ResourceRedirector/XUnity.ResourceRedirector.BepInEx.dll",
    "BepInEx/plugins/XUnity.ResourceRedirector/XUnity.ResourceRedirector.dll",
    "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt",
    "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt",
    "licenses/ElsinoreHanSans-NOTICE.txt", "licenses/ElsinoreHanSans-OFL.txt",
    "licenses/TextMeshPro-Unity-Companion-License.txt",
)
LICENSES = (
    "BepInEx-LICENSE.txt", "BepInEx.Harmony-LICENSE.txt", "ElsinoreHanSans-NOTICE.txt",
    "ElsinoreHanSans-OFL.txt", "ExIni-LICENSE.txt", "Harmony-LICENSE.txt", "HarmonyX-LICENSE.txt",
    "JetBrains.Annotations-LICENSE.txt", "Mono.Cecil-LICENSE.txt", "MonoMod-LICENSE.txt",
    "SimpleJSON-LICENSE.txt", "TextMeshPro-Unity-Companion-License.txt", "THIRD-PARTY-NOTICES.md",
    "UnityDoorstop-LGPL-2.1.txt", "UnityDoorstop-SOURCE.md", "XUnity.AutoTranslator-LICENSE.txt",
)
DOCS = {"README.md": "使用说明.txt", "INSTALL.md": "安装方法.txt",
        "TROUBLESHOOTING.md": "常见问题.txt", "CHANGELOG.md": "更新说明.txt"}
SCRIPTS = ("common.ps1", "install.ps1", "uninstall.ps1", "Install.cmd", "Uninstall.cmd")
SOURCE_ARCHIVE = "UnityDoorstop-4.5.0-source.zip"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def player_document(source: str) -> bytes:
    """从维护用Markdown生成Windows记事本可直接阅读的中文说明。"""
    for original, filename in DOCS.items():
        source = source.replace("](" + original + ")", "](" + filename + ")")
    def link(match):
        label, target = match.groups()
        return label if label == target else label + "（" + target + "）"
    source = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, source)
    source = re.sub(r"^#{1,6}\s+", "", source, flags=re.MULTILINE)
    source = re.sub(r"^> ?", "", source, flags=re.MULTILINE)
    source = source.replace("**", "").replace("`", "")
    return (source.rstrip().replace("\r\n", "\n").replace("\n", "\r\n") + "\r\n").encode("utf-8-sig")


def verify_versions(metadata: dict, installed_version: str, plugin_source: str) -> dict[str, str]:
    """公开补丁与内部插件独立编号，内部编号须匹配实际安装及插件声明。"""
    if set(metadata) != {"patch_version", "internal_version"}:
        raise ValueError("版本元数据字段不完整或含未知字段")
    for value in metadata.values():
        if not isinstance(value, str) or re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", value) is None:
            raise ValueError("版本必须为不含前缀的三段版本号")
    declared = re.search(r'\[BepInPlugin\("elsinorehan\.translationtoggle",\s*"[^"]+",\s*"([^"]+)"\)\]', plugin_source)
    if metadata["internal_version"] != installed_version or not declared or declared[1] != metadata["internal_version"]:
        raise ValueError("内部版本与实际安装或插件声明不一致")
    return {**metadata, "release_id": "v" + metadata["patch_version"]}


def safe_name(name: str) -> None:
    """只接受可直接解压的相对文件名，禁止夹带游戏、存档和私有目录。"""
    parts = name.split("/")
    if not name or name.startswith("/") or "\\" in name or ":" in name or any(p in ("", ".", "..") for p in parts):
        raise ValueError("归档路径不合法：" + name)
    lower = name.lower()
    forbidden = ("elsinore_data/", ".git/", "runtime/", "backups/", "isolated-save/", "__pycache__/")
    if any(p in lower for p in forbidden) or lower.endswith((".save", ".log", ".vdf", ".ttf", ".otf")):
        raise ValueError("归档含非补丁内容：" + name)
    if PurePosixPath(lower).name in ("elsinore.exe", "unityplayer.dll", "api-key.txt", ".env", "system.cfg"):
        raise ValueError("归档含游戏或私有文件：" + name)


def scan_secret(data: bytes, label: str, secrets: list[str]) -> None:
    rules = [name for name, pattern in PATTERNS.items() if pattern.search(data)]
    if any(secret.encode(enc) in data for secret in secrets for enc in ("utf-8", "utf-16-le", "utf-16-be")):
        rules.append("exact_local_secret")
    if rules:
        raise ValueError("内容扫描拒绝：" + label + "；规则=" + ",".join(rules))


def verify_offline_config(data: bytes) -> None:
    """兼容LF/CRLF，但不允许非空或重复端点掩盖真实生效值。"""
    lines = [line.strip() for line in data.decode("utf-8-sig").splitlines()]
    for key in ("Endpoint", "FallbackEndpoint"):
        values = [line.split("=", 1)[1].strip() for line in lines if line.split("=", 1)[0].strip() == key and "=" in line]
        if values != [""]:
            raise ValueError("离线翻译端点未关闭或存在重复项")


def main() -> None:
    package = ROOT / "runtime/package/ElsinoreHan-Sol"
    installed = read(ROOT / "runtime/evidence/ascension-empty-castle-install-verification-2026-10-19.json")
    if not installed["passed"] or not installed["installed"]:
        raise ValueError("尚无最终安装证明")
    versions = verify_versions(read(ROOT / "tools/release/version.json"), installed["plugin_version"],
                               (ROOT / "tools/patch/TranslationToggle.cs").read_text(encoding="utf-8-sig"))
    release_id = versions["release_id"]
    content: dict[str, bytes] = {}
    for name in PAYLOAD:
        data = (package / name).read_bytes()
        if digest(data) != installed["package_files"][name]:
            raise ValueError("运行文件与正式安装证明不符：" + name)
        content[name] = data
    assert len(content) == 39
    for name, filename in DOCS.items():
        content[filename] = player_document((ROOT / "docs/release" / name).read_text(encoding="utf-8-sig"))
    for name in SCRIPTS:
        content["ElsinoreHan/" + name] = (ROOT / "tools/release" / name).read_bytes()
    for name in LICENSES:
        content["ElsinoreHan/licenses/" + name] = (ROOT / "licenses" / name).read_bytes()

    license_proof = read(ROOT / "runtime/evidence/public-release-license-audit-2026-10-19.json")
    for entry in license_proof["public_license_files"]:
        data = content.get(entry["release_path"])
        if data is None or len(data) != entry["size"] or digest(data) != entry["sha256"]:
            raise ValueError("许可文件与来源审计不符：" + entry["release_path"])
    archive = ROOT / "runtime/build/public-license-audit" / SOURCE_ARCHIVE
    source_data = archive.read_bytes()
    if digest(source_data) != "7f0c963104aa08bf5fefef8ff85e7fecd8306838f5af3101487d9db4e9188d63":
        raise ValueError("Doorstop对应源码归档不符")
    content["ElsinoreHan/sources/" + SOURCE_ARCHIVE] = source_data

    entries = [{"path": name, "sha256": digest(content[name]), "size": len(content[name])} for name in PAYLOAD]
    # 仅认可已正式安装的旧词表，不泛化成任意历史文件或未知安装。
    dictionary = "BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt"
    old_text = content[dictionary].decode("utf-8-sig")
    for correction in read(ROOT / "translation/supplemental/ascension-dialogue-corrections.json"):
        line = encode(correction["source"]) + "=" + encode(correction["target"])
        previous = encode(correction["source"]) + "=" + encode(correction["previous_target"])
        if old_text.count(line) != 1:
            raise ValueError("无法准确重建已正式安装旧词表")
        old_text = old_text.replace(line, previous, 1)
    old_data = old_text.encode("utf-8")
    old_proof = read(ROOT / "runtime/evidence/post-burn-dialogue-install-verification-2026-10-19.json")
    if digest(old_data) != old_proof["dictionary_sha256"]:
        raise ValueError("旧词表重建与历史正式安装哈希不符")
    legacy = [{"path": dictionary, "sha256": digest(old_data), "size": len(old_data)}]
    manifest = {"schema_version": 1, "package_id": "ElsinoreHan", **versions,
                "files": entries, "legacy_files": legacy}
    content["ElsinoreHan/manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    secrets = local_secrets()
    for name, data in content.items():
        safe_name(name)
        scan_secret(data, name, secrets)
    with zipfile.ZipFile(io.BytesIO(source_data)) as z:
        nested = [i for i in z.infolist() if not i.is_dir()]
        if len(nested) != 55:
            raise ValueError("对应源码文件数不符")
        for item in nested:
            safe_name(item.filename)
            scan_secret(z.read(item), "Doorstop-source/" + item.filename, secrets)
    verify_offline_config(content["BepInEx/config/AutoTranslatorConfig.ini"])

    output = ROOT / "runtime/package/public-release"
    stage = output / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    # 只移除上一布局的四个已知说明，不递归清空暂存目录，额外文件仍应触发拒绝。
    for name in DOCS:
        previous_document = stage / "ElsinoreHan" / name
        if previous_document.is_file():
            previous_document.unlink()
    for name, data in content.items():
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    actual = {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()}
    if actual != set(content):
        raise ValueError("公开包暂存目录出现非白名单文件")
    filename = "ElsinoreHan-" + release_id + "-windows.zip"
    result = output / filename
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(content):
            z.writestr(name, content[name])
    with zipfile.ZipFile(result) as z:
        if set(z.namelist()) != set(content) or len(z.namelist()) != len(content):
            raise ValueError("ZIP清单有缺项、重复或额外项")
        for name, data in content.items():
            if z.read(name) != data:
                raise ValueError("ZIP字节不一致：" + name)
    archive_hash = digest(result.read_bytes())
    (output / "SHA256SUMS.txt").write_text(archive_hash + "  " + filename + "\n", encoding="ascii")
    report = {"date": "2026-10-19", **versions, "passed": True,
              "archive": result.relative_to(ROOT).as_posix(), "archive_sha256": archive_hash,
              "archive_size": result.stat().st_size, "flat_archive": True, "runtime_files": 39,
              "total_files": len(content), "source_archive_members": 55, "license_files": len(LICENSES),
              "local_secret_values_compared": len(secrets), "no_unlisted_files": True,
              "no_game_saves_or_backup_in_archive": True, "offline_endpoints_empty": True,
              "files": [{"path": n, "sha256": digest(b), "size": len(b)} for n, b in sorted(content.items())]}
    evidence = ROOT / ("runtime/evidence/public-release-" + versions["patch_version"] + "-package-verification-2026-10-19.json")
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("passed", "archive", "archive_size", "total_files", "runtime_files", "archive_sha256")}))


if __name__ == "__main__":
    main()
