"""从真实日志的冻结字符边界再生控件复用与缓存回归，不重新翻译正文。"""

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "translation/supplemental/othello-log-runtime-record.json"
BUILD = ROOT / "runtime/build/othello-log-followup"


def prepare() -> list[dict]:
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    source, target = record["source"], record["target"]
    assert hashlib.sha256(source.encode()).hexdigest() == record["source_sha256"]
    assert hashlib.sha256(target.encode()).hexdigest() == record["target_sha256"]
    header_end, translated_header_end = source.index("\n") + 1, target.index("\n") + 1
    cases = []
    previous_source, previous_target = header_end, translated_header_end
    for boundary in record["prefix_ends"]:
        end, translated_end = boundary["source_end"], boundary["target_end"]
        assert previous_source < end <= len(source) and previous_target < translated_end <= len(target)
        previous_source, previous_target = end, translated_end
        for header in (False, True):
            cases.append({"id": "current-real-prefix-" + ("header-" if header else "") + str(boundary["entry"]),
                          "source": source[0 if header else header_end:end],
                          "target": target[0 if header else translated_header_end:translated_end],
                          "origin": record["origin"]})
    assert previous_source == len(source) and previous_target == len(target)
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "cache-tests.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BUILD / "cache-cases.tsv").write_text("".join(row["id"] + "\t" + base64.b64encode(row["source"].encode()).decode()
                                                + "\t" + base64.b64encode(row["target"].encode()).decode() + "\n" for row in cases), encoding="utf-8")
    selected = {0, 1, 3, 7, 10, 16, 17, 20, 23, 26, 30, 43}
    representatives = [row for row in cases if row["id"].startswith("current-real-prefix-header-") and int(row["id"].split("-")[-1]) in selected]
    (ROOT / "translation/supplemental/othello-log-cache-tests.json").write_text(
        json.dumps(representatives, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cases


if __name__ == "__main__":
    print(json.dumps({"cases": len(prepare())}, ensure_ascii=False))
