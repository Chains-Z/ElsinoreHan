"""只读分析 Elsinore 的文字资源，并在本目录保存待译候选清单。"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import struct
from pathlib import Path

import pefile

GAME = Path(r"D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data")
OUTPUT = Path(__file__).resolve().parent
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
QUOTED = re.compile(r'"((?:\\.|[^"\\])*)"')
FIELDS = {"text", "slug", "title", "name", "long", "short", "categories", "description"}


def normalize(text: str) -> str:
    # 保留大小写与富文本标记，避免合并具有不同显示效果的原文。
    return re.sub(r"\s+", " ", text).strip()


def remove_comments(text: str) -> str:
    """删除字符串之外的注释，保留引号内的 URL 和转义符。"""
    return re.sub(
        r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/',
        lambda m: m.group() if m.group().startswith('"') else " ",
        text,
    )


def read_json(text: str):
    text = remove_comments(text)
    # 这些资源使用允许尾随逗号的 JSON 写法。
    text = re.sub(
        r'"(?:\\.|[^"\\])*"|,(\s*[}\]])',
        lambda m: m.group() if m.group().startswith('"') else m.group(1),
        text,
    )
    return json.loads(text)


def read_text_assets(data: bytes):
    """定位具有有效名称和 UTF-8 文本载荷的 TextAsset 候选对象。"""
    pattern = rb'([\x03-\x64])\x00\x00\x00([A-Za-z_][A-Za-z0-9_.-]{2,99})'
    seen = set()
    for match in re.finditer(pattern, data):
        length = match.group(1)[0]
        name = match.group(2)
        if len(name) != length:
            continue
        position = (match.start() + 4 + length + 3) & ~3
        if position + 4 > len(data):
            continue
        size = struct.unpack_from("<I", data, position)[0]
        if not 100 <= size <= min(3_000_000, len(data) - position - 4):
            continue
        body = data[position + 4 : position + 4 + size]
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if not (text.lstrip().startswith(("{", "//elsinore", "//", "<html"))):
            continue
        digest = hashlib.sha256(body).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        yield name.decode("ascii"), digest, text


def read_user_strings(path: Path):
    """读取 .NET #US 常量池，不加载或运行游戏程序集。"""
    image = pefile.PE(str(path), fast_load=True)
    try:
        header = image.get_data(image.OPTIONAL_HEADER.DATA_DIRECTORY[14].VirtualAddress, 72)
        address, size = struct.unpack_from("<II", header, 8)
        metadata = image.get_data(address, size)
    finally:
        image.close()
    assert metadata[:4] == b"BSJB"
    version_size = struct.unpack_from("<I", metadata, 12)[0]
    position = (16 + version_size + 3) & ~3
    count = struct.unpack_from("<H", metadata, position + 2)[0]
    position += 4
    streams = {}
    for _ in range(count):
        offset, size = struct.unpack_from("<II", metadata, position)
        position += 8
        end = metadata.index(0, position)
        name = metadata[position:end].decode("ascii")
        position = (end + 4) & ~3
        streams[name] = metadata[offset : offset + size]
    data = streams["#US"]
    position = 1
    while position < len(data):
        start = position
        first = data[position]
        if first < 128:
            size, position = first, position + 1
        elif first < 192:
            size = ((first & 63) << 8) | data[position + 1]
            position += 2
        else:
            size = ((first & 31) << 24) | (data[position + 1] << 16) | (data[position + 2] << 8) | data[position + 3]
            position += 4
        if not size:
            continue
        raw = data[position : position + size]
        position += size
        if len(raw) != size:
            raise ValueError("字符串常量池长度不匹配")
        yield start, raw[:-1].decode("utf-16-le")


def main():
    entries = {}
    resource_counts = collections.Counter()
    parse_errors = []

    def add(text: str, origin: str, category: str):
        text = text.strip()
        if not re.search(r"[A-Za-z]", text):
            return
        key = normalize(text)
        item = entries.setdefault(key, {"text": text, "origins": [], "categories": []})
        if origin not in item["origins"]:
            item["origins"].append(origin)
        if category not in item["categories"]:
            item["categories"].append(category)

    def visit(value, origin: str, field: str = ""):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, origin, key)
        elif isinstance(value, list):
            for child in value:
                visit(child, origin, field)
        elif isinstance(value, str) and field in FIELDS:
            add(value, f"{origin}:{field}", "resource_ui")

    assets = list(read_text_assets((GAME / "resources.assets").read_bytes()))
    for name, digest, text in assets:
        origin = f"resources.assets:{name}:{digest[:12]}"
        if name.startswith("scenes") and name != "scenes_declarations":
            for match in QUOTED.finditer(remove_comments(text)):
                value = match.group(1).replace(r"\n", "\n").replace(r'\"', '"').replace(r"\\", "\\")
                if len(WORD.findall(value)) >= 2 and re.search(r"\s", value):
                    add(value, origin, "dialogue")
                    resource_counts[name] += 1
        elif name in {"bios", "closeups", "leads", "information", "knowledge", "endings", "characters"}:
            try:
                visit(read_json(text), origin)
            except json.JSONDecodeError as error:
                parse_errors.append({"asset": name, "error": str(error)})
        elif name == "name_mapping":
            for value in read_json(text).values():
                if isinstance(value, str):
                    add(value, origin, "resource_ui")

    primary = list(entries.values())
    primary_words = sum(len(WORD.findall(item["text"])) for item in primary)
    primary_chars = sum(len(item["text"]) for item in primary)
    assembly_total = 0
    assembly_review = []
    for offset, text in read_user_strings(GAME / "Managed" / "Assembly-CSharp.dll"):
        assembly_total += 1
        key = normalize(text)
        origin = f"Assembly-CSharp.dll:#US:{offset}"
        if key in entries:
            entries[key]["origins"].append(origin)
        elif len(text) >= 12 and re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", text):
            assembly_review.append({"text": text, "origin": origin})

    metrics = {
        "game_path": str(GAME),
        "method": "本地静态提取、按空白规范化去重；程序集额外字符串需审核",
        "unique_text_asset_candidates": len(assets),
        "primary_entries": len(primary),
        "primary_english_words": primary_words,
        "primary_characters": primary_chars,
        "dialogue_entries": sum("dialogue" in item["categories"] for item in primary),
        "resource_ui_entries": sum("resource_ui" in item["categories"] for item in primary),
        "assembly_user_string_count": assembly_total,
        "assembly_additional_review_entries": len(assembly_review),
        "assembly_additional_review_words": sum(len(WORD.findall(item["text"])) for item in assembly_review),
        "parse_errors": parse_errors,
        "limitations": ["还未验证游戏内文字拦截覆盖率", "TextAsset 通过载荷结构定位，未逐对象验证 Unity 类型", "可能包含未启用的剧情分支或测试场景", "未统计图片中的文字"],
    }
    (OUTPUT / "text_inventory.json").write_text(json.dumps(primary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "assembly_review.json").write_text(json.dumps(assembly_review, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
