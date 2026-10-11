"""生成受控思源字体字符集：GB2312、支持的拉丁字符和当前玩家译文。"""

import argparse
import json
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
FONT_TEST_ID = "u00027-aef783a99d65"


def prepare(source: Path, translations: Path, output: Path) -> None:
    with TTFont(source) as font:
        supported = set(font.getBestCmap())
    characters = {chr(code) for code in supported if 32 <= code < 0x250}
    for lead in range(0xA1, 0xF8):
        for trail in range(0xA1, 0xFF):
            try:
                characters.add(bytes((lead, trail)).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    rows = json.loads(translations.read_text(encoding="utf-8"))
    for row in rows:
        # 该源是程序保留的字体样本，包含思源不支持的拉丁字符；不是玩家正文。
        if row["id"] != FONT_TEST_ID:
            characters.update(character for character in row["target"] if not character.isspace())
    missing = sorted(ord(character) for character in characters if ord(character) not in supported)
    if missing:
        raise ValueError("当前玩家译文或GB2312缺字：" + ", ".join(f"U+{code:04X}" for code in missing))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(sorted(characters)), encoding="utf-8", newline="\n")
    print(json.dumps({"character_count": len(characters), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "runtime/vendor/fonts/source-han-sans/SourceHanSansSC-Regular.otf")
    parser.add_argument("--translations", type=Path, default=ROOT / "translation/sol-full-2026-10-09/translations.json")
    parser.add_argument("--output", type=Path, default=ROOT / "runtime/build/font-replacement/font-characters.txt")
    args = parser.parse_args()
    prepare(args.source, args.translations, args.output)
