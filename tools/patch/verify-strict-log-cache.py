"""核验预置混合缓存后的真实TMP复用和F8回归，不冒称实际现场缓存采集。"""

import argparse
import hashlib
import json
from pathlib import Path


def analyze(report: str, cases: bytes) -> dict:
    rows = [line.split("\t") for line in report.splitlines() if line]
    expected = [line.split("\t")[0] for line in cases.decode("utf-8").splitlines() if line]
    actual = [row for row in rows if row[0] == "CASE"]
    checks = {
        "fixture_hash_matches": [row[1:] for row in rows if row[0] == "SOURCE_SHA256"] == [[hashlib.sha256(cases).hexdigest()]],
        "every_case_once": bool(expected) and len(expected) == len(set(expected)) == len(actual)
        and {row[1] for row in actual if len(row) > 1} == set(expected),
        "seeded_cache_repaired_and_f8_exact": bool(actual) and all(len(row) == 7 and row[2:] == ["True"] * 5 for row in actual),
        "unknown_atom_rejected": [row[1:] for row in rows if row[0] == "UNKNOWN_REJECTED"] == [["True"]],
        "summary_complete": [row[1:] for row in rows if row[0] == "SUMMARY"] == [["True", str(len(expected))]],
    }
    return {"passed": all(checks.values()), "checks": checks, "count": len(actual),
            "limitation": "混合缓存由探针预置，验证失效机制与修复，不代表已读取用户现场内存缓存"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.evidence.read_text(encoding="utf-8-sig"), args.cases.read_bytes())
    args.evidence.with_suffix(".verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)
