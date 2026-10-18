"""从已公开发行包恢复维护依赖；离线核验，不安装游戏、不读取存档。"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_archive(path, expected_sha256, expected_files):
    """先核对整包和所有条目，再允许恢复文件。"""
    if digest(path.read_bytes()) != expected_sha256:
        raise ValueError("发行ZIP与已记录的SHA256不符")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected_files):
            raise ValueError("发行ZIP存在缺项、重复或额外条目")
        content = {name: archive.read(name) for name in names}
    for name, data in content.items():
        entry = expected_files[name]
        if len(data) != entry["size"] or digest(data) != entry["sha256"]:
            raise ValueError("发行ZIP条目与核验记录不符：" + name)
    return content


def write_missing(root, files):
    """全部目标预检成功后仅补缺失文件，不覆盖已有修改或写出runtime。"""
    root = root.resolve()
    runtime = root / "runtime"
    pending = []
    for relative, data in files.items():
        target = root / relative
        if (not relative.startswith("runtime/") or
                not target.resolve().is_relative_to(runtime) or
                any(part in (".", "..") for part in relative.split("/"))):
            raise ValueError("恢复目标越界：" + relative)
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError("已有文件与发行基线不同，拒绝覆盖：" + relative)
        else:
            pending.append((target, data))
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return len(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="从GitHub v1.0.0下载的完整windows.zip")
    args = parser.parse_args()
    baseline_dir = ROOT / "runtime/evidence/recovery-baseline"
    baseline = read(baseline_dir / "manifest.json")
    proof = read(ROOT / "runtime/evidence/public-release-1.0.0-package-verification-2026-10-19.json")
    if proof["archive_sha256"] != baseline["release_sha256"]:
        raise ValueError("当前包证明与归档基线不同，请人工核对发行版本")
    content = checked_archive(args.archive, baseline["release_sha256"],
                              {row["path"]: row for row in proof["files"]})
    metadata = {}
    for entry in baseline["files"]:
        data = (baseline_dir / entry["path"]).read_bytes()
        if len(data) != entry["size"] or digest(data) != entry["sha256"]:
            raise ValueError("归档元数据不符：" + entry["path"])
        metadata[entry["path"]] = data
    spec = importlib.util.spec_from_file_location("recovery_public_builder", ROOT / "tools/release/build-public-release.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.verify_offline_config(content["BepInEx/config/AutoTranslatorConfig.ini"])
    installed = read(ROOT / "runtime/evidence/ascension-empty-castle-install-verification-2026-10-19.json")
    for name in builder.PAYLOAD:
        if digest(content[name]) != installed["package_files"][name]:
            raise ValueError("运行文件不匹配正式安装证明：" + name)
    builder.verify_plugin_sources(
        {name: (ROOT / "tools/patch" / name).read_bytes() for name in builder.PLUGIN_SOURCES},
        (ROOT / "tools/patch/build-toggle.ps1").read_text(encoding="utf-8-sig"),
        json.loads(metadata["plugin-build.json"].decode("utf-8-sig")), installed["plugin_sha256"])
    font_proof = json.loads(metadata["font-assembly.json"].decode("utf-8-sig"))
    if (digest(content["elsinorehan_sans_sdf_u2018"]) != font_proof["bundle_sha256"] or
            digest(metadata["font-bake.json"]) != font_proof["bake_metadata_sha256"]):
        raise ValueError("字体产物与原始装配／烘焙证明不符")

    files = {"runtime/package/ElsinoreHan-Sol/" + name: content[name] for name in builder.PAYLOAD}
    for name in builder.PAYLOAD:
        if name.startswith("BepInEx/core/"):
            vendor = "XUnity" if name.endswith("/XUnity.Common.dll") else "BepInEx5"
        elif name.startswith("BepInEx/plugins/") and not name.endswith("/ElsinoreHan.TranslationToggle.dll"):
            vendor = "XUnity"
        elif name in (".doorstop_version", "changelog.txt", "doorstop_config.ini", "winhttp.dll"):
            vendor = "BepInEx5"
        else:
            continue
        files["runtime/vendor/" + vendor + "/" + name] = content[name]
    files.update({
        "runtime/build/ElsinoreHan.TranslationToggle.dll": content["BepInEx/plugins/ElsinoreHan.TranslationToggle.dll"],
        "runtime/build/translation-toggle-build.json": metadata["plugin-build.json"],
        "runtime/vendor/fonts/elsinorehan_sans_sdf_u2018": content["elsinorehan_sans_sdf_u2018"],
        "runtime/vendor/fonts/elsinorehan_sans_sdf_u2018.verification.json": metadata["font-assembly.json"],
        "runtime/vendor/XUnity-source-master/XUnity.AutoTranslator-master/LICENSE": content["XUnity-LICENSE"],
        "runtime/build/public-license-audit/" + builder.SOURCE_ARCHIVE:
            content["ElsinoreHan/sources/" + builder.SOURCE_ARCHIVE],
    })
    restored = write_missing(ROOT, files)
    print(json.dumps({"passed": True, "release_tag": baseline["release_tag"],
                      "runtime_files": len(builder.PAYLOAD), "restored_files": restored,
                      "verified_files": len(files), "game_or_saves_accessed": False}))


if __name__ == "__main__":
    main()
