"""依据人工审定的双源校订，生成真实姓名及显示封套的消费者夹具。"""

from audit_dialect_dialogue import extract_rows
from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, digest, read, save, short_name
from prepare_ending_style_followup import project_current


DIRECTORY = ROOT / "translation/supplemental"


def main():
    plans = read(DIRECTORY / "source-variant-review.json")
    changes = read(DIRECTORY / "source-variant-corrections.json")
    followup_path = DIRECTORY / "place-and-dialogue-corrections.json"
    followups = read(followup_path) if followup_path.exists() else []
    followups += read(DIRECTORY / "playmaster-title-corrections.json")
    checked = apply_supplemental([
        {"id": row["original_id"], "source": row["source"], "target": row["previous_target"]}
        for row in changes], changes)
    assert len(checked) == len(changes)
    targets = {row["source"]: row for row in read(ROOT / "translation/sol-full-2026-10-09/translations.json")}
    dialogue, _ = extract_rows(list(targets.values()))
    owners = {(row["actor"], row["source"], row["runtime_source"]): row for row in dialogue}
    assembly = {row["source"] for row in read(ROOT / "analysis/ui-audit/assembly-strings.json")}
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    changed_sources = {row["source"] for row in changes}
    covered = set()
    cases = []
    for plan in plans:
        actor, source, runtime = plan["actor"], plan["source"], plan["runtime_source"]
        owner = owners[(actor, source, runtime)]
        assert runtime in assembly
        assert owner["origins"] == plan["origins"]
        assert source in changed_sources or runtime in changed_sources
        covered.update({source, runtime} & changed_sources)
        name = short_name(actor, mapping)
        translated_name = SPECIAL_NAMES.get(name) or targets[name]["target"]
        # 原审查记录保留阶段快照，消费者经精确旧值承接用户后续校订。
        expected_rows = apply_supplemental([
            {"id": targets[source]["id"], "source": source, "target": plan["canonical_target"]},
            {"id": targets[runtime]["id"], "source": runtime, "target": plan["expected_runtime_target"]},
        ], [row for row in followups if row["source"] in {source, runtime}])
        resource_target, runtime_target = (row["target"] for row in project_current(expected_rows))
        for kind, text, expected in (
            ("resource", source, resource_target),
            ("runtime", runtime, runtime_target),
            ("dialogue", "<line-height=90%>" + runtime,
             "<line-height=90%>" + runtime_target),
            ("log", "<b>" + name + ":</b> <indent=16%>" + runtime,
             "<b>" + translated_name + ":</b> <indent=16%>" + runtime_target),
        ):
            cases.append({"id": "source-variant-" + str(plan["review_index"]) + "-" + kind,
                          "source": text, "target": expected, "source_sha256": digest(text),
                          "origins": owner["origins"]})
    assert covered == changed_sources
    assert len(cases) == 4 * len(plans)
    assert len({row["id"] for row in cases}) == len(cases)
    save(DIRECTORY / "source-variant-tests.json", cases)
    print(f"已核对{len(plans)}组真实双源、{len(changes)}条准确旧值，生成{len(cases)}项消费者夹具")


if __name__ == "__main__":
    main()
