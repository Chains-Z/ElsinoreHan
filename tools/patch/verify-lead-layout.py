"""验证真实任务按钮在多次F8切换后的背景覆盖和交互状态。"""
import argparse
import base64
import json
from pathlib import Path


def analyze(report: str) -> dict:
    """缺行、失败、背景未扩展及交互状态改变均不得判为通过。"""
    rows = [line.split('\t') for line in report.splitlines()]
    expected = next(row for row in rows if row[0] == 'EXPECTED')
    count, modes = map(int, expected[1:])
    items = [row for row in rows if row[0] == 'ITEM']
    checks = {
        'complete': ['STATUS', 'COMPLETE'] in rows,
        'all_items_and_modes': len(items) == count * modes and {(int(row[1]), int(row[2])) for row in items} == {(mode, index) for mode in range(modes) for index in range(count)},
        'background_centered': all(abs(float(row[10])) < 0.02 for row in items),
        'geometry_and_interaction': all(len(row) == 19 and all(value == 'True' for value in row[11:]) for row in items),
        'all_font_sizes_36': bool(items) and all(float(row[4]) == 36 for row in items),
    }
    texts = {(int(row[1]), int(row[2])): base64.b64decode(row[3]).decode() for row in items}
    checks['original_and_translation_distinct'] = all(texts.get((0, index)) != texts.get((1, index)) for index in range(count))
    checks['repeated_modes_restore_exact_text'] = all(texts.get((mode, index)) == texts.get((mode % 2, index)) for mode in range(modes) for index in range(count))
    return {'passed': all(checks.values()), 'checks': checks, 'items': count, 'modes': modes, 'records': len(items)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze(args.report.read_text(encoding='utf-8-sig'))
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
