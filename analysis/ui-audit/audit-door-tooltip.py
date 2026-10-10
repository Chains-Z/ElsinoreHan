"""从真实资源复现门口提示字段检查，仅输出精简来源摘要。"""
import hashlib
import importlib.util
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("audit_resources", ROOT / "analysis/ui-audit/audit-resources.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def read_doors():
    """读取全部序列化文件中的门组件，不访问存档。"""
    files = {p.name: audit.read_serialized(p) for p in audit.GAME.iterdir()
             if p.name.endswith(".assets") or re.fullmatch(r"level\d+", p.name)}
    scripts = {}
    for name, data in files.items():
        for path_id, obj in data["objects"].items():
            if obj["class_id"] != 115:
                continue
            raw = data["data"][obj["offset"]:obj["offset"] + obj["size"]]
            _, pos = audit.read_string(raw, 0)
            classname, pos = audit.read_string(raw, pos + 20)
            scripts[(name, path_id)] = classname
    doors = []
    for name, data in files.items():
        for path_id, obj in data["objects"].items():
            if obj["class_id"] != 114:
                continue
            raw = data["data"][obj["offset"]:obj["offset"] + obj["size"]]
            file_id, script_id = struct.unpack_from("<iq", raw, 16)
            script_file = Path(data["externals"][file_id - 1]).name if file_id else name
            if scripts.get((script_file, script_id)) != "DoorMarker":
                continue
            _, pos = audit.read_string(raw, 28)
            doors.append({"file": name, "path_id": path_id, "raw": raw, "pos": pos,
                          "absolute_offset": obj["offset"], "file_sha256": hashlib.sha256(data["data"]).hexdigest()})
    return len(files), doors


def main():
    subprocess.run(["pwsh.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(ROOT / "analysis/ui-audit/audit-door-tooltip-il.ps1")], check=True)
    file_count, doors = read_doors()
    sources = []
    rejected_nonempty = 0
    for door in doors:
        for offset, descriptor in audit.door_marker_string_fields(door["raw"], door["pos"]).items():
            source, _ = audit.read_string(door["raw"], offset)
            if descriptor["decision"] == "player_facing" and source:
                sources.append({"source": source, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                                "file": door["file"], "file_sha256": door["file_sha256"],
                                "path_id": door["path_id"], "field": descriptor["field"],
                                "object_offset": offset, "absolute_offset": door["absolute_offset"] + offset,
                                "serialized_object_sha256": hashlib.sha256(door["raw"]).hexdigest(),
                                "ui_path": descriptor["ui_path"]})
            elif source:
                rejected_nonempty += 1
    il = json.loads((ROOT / "runtime/build/out-to-sea-audit/ui-path-il.json").read_text(encoding="utf-8"))
    getter = next(m for m in il["methods"] if "IInteractable.get_Tooltip" in m["method"])
    report = {"schema_version": 1, "verification_method": "只读原资源和程序集；未启动游戏或读取存档",
              "serialized_file_count": file_count, "door_count": len(doors),
              "field_checks": len(doors) * 4, "nonempty_internal_fields_rejected": rejected_nonempty,
              "nonempty_player_sources": sources, "recommended_target": "出海",
              "assembly": {"path": il["assembly"], "sha256": il["sha256"]},
              "tooltip_getter": getter}
    out = ROOT / "analysis/ui-audit/out-to-sea-source-audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"door_count": len(doors), "field_checks": len(doors) * 4,
                      "nonempty_player_sources": len(sources), "internal_fields_rejected": rejected_nonempty}))


if __name__ == "__main__":
    main()
