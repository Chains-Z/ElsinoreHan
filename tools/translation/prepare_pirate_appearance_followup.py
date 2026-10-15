"""核对真实海盗外貌描述，生成裸句、角色日志与相邻强盗词条回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, read, save


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    rows, _ = extract_rows(translations)
    row = next(row for row in rows if row["id"] == "p14494-606bd47163df")
    target = "看起来是个粗犷、不修边幅的人。我想，大海这位女主人可不好伺候……"
    assert row["actor"] == "ophelia" and row["target"] == target
    assert row["origins"] == [
        {"asset": "scenes_smalltalk", "asset_sha256": "aef8dad0e3b11e6d39b3c0f537430008bfbb5cf05a11b4ee863c86da42b918dd",
         "scene": "ST_Generic_Pirate", "line": 166},
        {"asset": "scenes_smalltalk", "asset_sha256": "ab46b35e4fae1f3e4f5e6437fde97a9c29d32a4163443af8e8905374d7fac6d1",
         "scene": "ST_Generic_Pirate", "line": 165},
    ]
    brigand = next(row for row in rows if row["id"] == "p14492-f7e7a4b37b98")
    assert brigand["target"] == "看起来是个不好惹、不修边幅的人。我最好别插手。"
    cases = [
        {"id": "pirate-appearance-leaf", "source": row["runtime_source"], "target": target, "origins": row["origins"]},
        {"id": "pirate-appearance-log", "source": "<b>Ophelia:</b> <indent=16%>" + row["runtime_source"],
         "target": "<b>奥菲莉娅:</b> <indent=16%>" + target, "origins": row["origins"]},
        {"id": "brigand-appearance-unchanged", "source": brigand["runtime_source"],
         "target": brigand["target"], "origins": brigand["origins"]},
    ]
    save(ROOT / "translation/supplemental/pirate-appearance-tests.json", cases)
    save(ROOT / "runtime/build/pirate-appearance/source-audit.json", {"pirate": row, "brigand": brigand})
    print("3项海盗外貌及强盗原译消费者用例已生成")


if __name__ == "__main__":
    main()
