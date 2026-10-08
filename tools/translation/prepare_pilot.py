"""从本机真实资料制作 VNText 试译输入，不调用模型或改写游戏文件。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
import analyze

SECTION = re.compile(r"^\s*\{([A-Za-z_][A-Za-z0-9_]*)\}\s*$")
DIALOGUE = re.compile(
    r'^\s*([A-Za-z_][A-Za-z0-9_]*):\s*'
    r'((?:(?:\[[^\]\r\n]*\]|\{[^}\r\n]*\})\s*)*)'
    r'"((?:\\.|[^"\\])*)"\s*$'
)
ESCAPES = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}


def decode_dialogue(text: str) -> str:
    """只解释已知脚本转义，未知序列原样保留。"""
    return re.sub(r"\\(.)", lambda m: ESCAPES.get(m[1], m[0]), text)


def mask_comments(text: str) -> str:
    """遮盖字符串以外的注释，并保留换行以追溯原始行号。"""
    return re.sub(
        r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/',
        lambda m: m[0] if m[0].startswith('"') else re.sub(r"[^\r\n]", " ", m[0]),
        text,
    )


def read_dialogues(body: str, digest: str, names: dict) -> list[dict]:
    """保守提取明确的单行角色对白，不猜测其他脚本语法。"""
    rows = []
    scene = ""
    for number, line in enumerate(mask_comments(body).splitlines(), 1):
        section = SECTION.fullmatch(line)
        if section:
            scene = section[1]
            continue
        match = DIALOGUE.fullmatch(line)
        if not match or not scene:
            continue
        speaker, cues, source = match.groups()
        text = decode_dialogue(source)
        rows.append({
            "id": f"scenes:{digest[:12]}:{number}",
            "scene": scene,
            "speaker_id": speaker,
            "name": names.get(speaker, speaker),
            "message": text,
            "source_line": number,
            "source_asset_sha256": digest,
            "source_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "acting_cues": cues.strip(),
        })
    return rows


def choose_scene_groups(rows: list[dict], target: int) -> list[dict]:
    """从开篇角色对白起按脚本段落选取，保留完整段落。"""
    start = next(i for i, row in enumerate(rows) if row["scene"] == "Spine_OpheliaAloneStarter")
    result = []
    previous = ""
    for row in rows[start:]:
        if row["scene"] != previous and len(result) >= target:
            break
        result.append(row)
        previous = row["scene"]
    return result


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-data", type=Path, default=analyze.GAME)
    parser.add_argument("--output", type=Path, default=ROOT / "translation" / "pilot")
    parser.add_argument("--dialogue-target", type=int, default=120)
    args = parser.parse_args()
    if args.dialogue_target < 1:
        parser.error("dialogue-target 必须为正数")
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output == ROOT:
        parser.error("输出须位于项目内的独立目录")
    if output.exists() and any(output.iterdir()):
        parser.error("输出目录非空，请使用新的目录，避免覆盖译文或已有样本")
    assets = list(analyze.read_text_assets((args.game_data / "resources.assets").read_bytes()))
    mappings = [analyze.read_json(body) for name, _, body in assets if name == "name_mapping"]
    if not mappings:
        raise ValueError("未找到真实角色名称映射")
    # 最大剧情资源适合试译；这不证明它是游戏实际加载的版本。
    candidates = [(digest, body) for name, digest, body in assets if name == "scenes"]
    digest, body = max(candidates, key=lambda item: len(item[1]))
    rows = choose_scene_groups(read_dialogues(body, digest, mappings[-1]), args.dialogue_target)
    grouped = {}
    for row in rows:
        grouped.setdefault(row["scene"], []).append(row)
    manifest = []
    for scene, members in grouped.items():
        filename = f"dialogue/{scene}.json"
        write_json(output / "input" / filename, [
            {"name": row["name"], "message": row["message"]} for row in members
        ])
        for index, row in enumerate(members):
            manifest.append({"file": filename, "index": index, **row})
    inventory = json.loads((ROOT / "analysis" / "text_inventory.json").read_text(encoding="utf-8"))
    ui_rows = [item for item in inventory if "resource_ui" in item["categories"]][:30]
    ui_filename = "documents/resource_ui.json"
    write_json(output / "input" / ui_filename, [{"message": row["text"]} for row in ui_rows])
    for index, row in enumerate(ui_rows):
        text = row["text"]
        text_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        manifest.append({
            "file": ui_filename, "index": index, "id": f"inventory:{text_digest[:16]}",
            "message": text, "source_text_sha256": text_digest, "origins": row["origins"],
        })
    write_json(output / "manifest.json", {
        "format": "VNText", "source": "本地真实游戏资源；未调用模型",
        "limitations": [
            "剧情资源按最大载荷选择，尚未证明是实际加载版本",
            "保留脚本顺序，条件分支之间不能推定为同一次对话",
            "只解析明确的单行角色对白，不是完整提取器",
            "资料样本来自现有候选清单，字段来源仍需审核",
            "VNText 工具输出可能丢弃元数据；必须保留本清单以关联原文",
        ],
        "dialogue_count": len(rows), "document_count": len(ui_rows),
        "entries": manifest,
    })
    print(json.dumps({"output": str(output), "dialogue": len(rows), "documents": len(ui_rows),
                      "scene_files": len(grouped), "model_calls": 0}, ensure_ascii=True))


if __name__ == "__main__":
    main()
