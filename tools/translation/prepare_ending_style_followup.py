"""核对书名号和谢幕并列句的准确覆盖链，生成真实运行消费者夹具。"""

from export_sol_full import apply_supplemental
from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, digest, read, save, short_name
from source_variant_generation import project_subset, reading_overrides


DIRECTORY = ROOT / "translation/supplemental"
LAYERS = ("ending-style-corrections.json", "ghost-regret-corrections.json", "source-variant-corrections.json", "place-and-dialogue-corrections.json", "playmaster-title-corrections.json", "victory-dinner-corrections.json", "playmaster-tone-corrections.json", "post-burn-dialogue-corrections.json", "ascension-dialogue-corrections.json")


def project_current(rows):
    return project_subset(rows, read(DIRECTORY / "canonical-variant-translations.json"),
                          read(DIRECTORY / "generated-variant-bindings.json"))


def reading_generated(reviewed):
    from prepare_all_endings_followup import apply_reading_followup, paragraph_overrides
    sources = {row[key] for row in reviewed for key in ("source", "runtime_source")}
    overrides = paragraph_overrides(reading_overrides(sources,
        read(DIRECTORY / "canonical-variant-translations.json"), read(DIRECTORY / "generated-variant-bindings.json")))
    used = set()
    result = [apply_reading_followup(row, overrides, used) for row in reviewed]
    assert used == set(overrides)
    return result


def apply_styles(rows):
    """已审定的旧阶段条目经准确旧值校验后承接当前文字校订。"""
    sources = {row["source"] for row in rows}
    for filename in LAYERS:
        path = DIRECTORY / filename
        if path.exists():
            rows = apply_supplemental(rows, [row for row in read(path) if row["source"] in sources])
    return project_current(rows)


def reading_style(reviewed):
    """承接历史审查与姓名校订后，分别核对资源及编译源的精确旧译。"""
    from prepare_all_endings_followup import apply_reading_followup, paragraph_overrides
    sources = {row[key] for row in reviewed for key in ("source", "runtime_source")}
    for filename in LAYERS:
        path = DIRECTORY / filename
        if not path.exists():
            continue
        changes = [row for row in read(path) if row["source"] in sources]
        overrides, used = paragraph_overrides(changes), set()
        reviewed = [apply_reading_followup(row, overrides, used) for row in reviewed]
        assert used == set(overrides)
    return reading_generated(reviewed)


def main():
    changes = read(DIRECTORY / "ending-style-corrections.json")
    checked = apply_supplemental([
        {"id": row["original_id"], "source": row["source"], "target": row["previous_target"]}
        for row in changes], changes)
    targets = {row["source"]: row for row in read(ROOT / "translation/sol-full-2026-10-09/translations.json")}
    manifest = {row["source"]: row for row in read(ROOT / "translation/sol-full-2026-10-09/manifest.json")["entries"]}
    assembly = {row["source"]: row for row in read(ROOT / "analysis/ui-audit/assembly-strings.json")}
    dialogue, _ = extract_rows(list(targets.values()))
    actual = {row["source"] for row in dialogue} | {row["runtime_source"] for row in dialogue}
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    cases = []
    for row, merged in zip(changes, checked):
        source = row["source"]
        assert source in actual and source in targets
        assert source in manifest or source in assembly
        assert targets[source]["target"] == merged["target"] == row["target"]
        assert targets[source]["id"] == row["original_id"]
        owner = next(item for item in dialogue if source in (item["source"], item["runtime_source"]))
        name = short_name(owner["actor"], mapping)
        translated_name = SPECIAL_NAMES.get(name) or targets[name]["target"]
        for kind, text, target in (
            ("leaf", source, row["target"]),
            ("dialogue", "<line-height=90%>" + source, "<line-height=90%>" + row["target"]),
            ("log", "<b>" + name + ":</b> <indent=16%>" + source,
             "<b>" + translated_name + ":</b> <indent=16%>" + row["target"]),
        ):
            cases.append({"id": row["id"] + "-" + kind, "source": text, "target": target,
                          "source_sha256": digest(text), "origins": row["origins"]})
    books = [row for row in targets.values() if "命运之书" in row["target"]]
    assert len(books) == 49
    for row in books:
        assert row["target"].count("命运之书") == row["target"].count("《命运之书》")
        assert "《《" not in row["target"] and "》》" not in row["target"]
        cases.append({"id": "book-title-" + row["id"], "source": row["source"], "target": row["target"]})
    assert len(changes) == 22 and len(cases) == 115
    save(DIRECTORY / "ending-style-tests.json", cases)
    print("21条书名号、1条谢幕并列句及49条全局书名检查通过；生成115项消费者夹具")


if __name__ == "__main__":
    main()
