"""核查跨剧姓名的准确覆盖链、真实源和运行组合，生成离线消费者夹具。"""

import json
import re

from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import (
    DIALOGUE, SCENE, ROOT, GAME_RESOURCE, dialogue_source, digest, read, read_text_assets,
    save, short_name, source_rows,
)
from analyze import read_json


DIRECTORY = ROOT / "translation/supplemental"


def apply_names(rows):
    """让历史审查保留快照，通过准确旧译承接本轮姓名修订。"""
    sources = {row["source"] for row in rows}
    changes = [row for row in read(DIRECTORY / "shakespeare-name-corrections.json")
               if row["source"] in sources]
    from prepare_ending_style_followup import apply_styles
    return apply_styles(apply_supplemental(rows, changes))


def reading_names(reviewed):
    """分别承接资源和编译源的姓名，不用一种变体替另一种兜底。"""
    from prepare_all_endings_followup import apply_reading_followup, paragraph_overrides
    sources = {row[key] for row in reviewed for key in ("source", "runtime_source")}
    changes = [row for row in read(DIRECTORY / "shakespeare-name-corrections.json")
               if row["source"] in sources]
    overrides, used = paragraph_overrides(changes), set()
    result = [apply_reading_followup(row, overrides, used) for row in reviewed]
    assert used == set(overrides)
    return result


def environment_cases(targets):
    """从真实调查脚本和全部文书重新取源，含短发言及资源标点变体。"""
    rows, cases, seen = [], [], set()
    for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes()):
        if name not in ("scenes_enviro", "scenes_background", "closeups"):
            continue
        if name == "closeups":
            for document in read_json(text)["closeups"]:
                for field in ("title", "text"):
                    source = document[field]
                    rows.append({"source": source, "runtime_source": source,
                                 "origin": {"asset": name, "asset_sha256": sha,
                                            "record_id": document["id"], "field": field}})
        else:
            for match in DIALOGUE.finditer(text):
                source = json.loads('"' + match["text"] + '"')
                scene = list(SCENE.finditer(text[:match.start()]))[-1][1]
                rows.append({"source": source, "runtime_source": dialogue_source(match["actor"], source),
                             "origin": {"asset": name, "asset_sha256": sha, "scene": scene,
                                        "line": text[:match.start()].count("\n") + 1}})
    for row in rows:
        for source in sorted({row["source"], row["runtime_source"]}):
            if source in seen:
                continue
            seen.add(source)
            # 笔记资源的终LF由实际XUnity空白处理消费，保留原始输入作回归。
            entry = targets.get(source) or targets.get(source.strip())
            assert entry is not None or source == "..."
            cases.append({"id": "environment-" + str(len(cases)), "source": source,
                          "target": entry["target"] if entry else "...", "origins": [row["origin"]]})
    assert len(rows) == 671 and len({row["source"] for row in rows}) == 451
    assert len(cases) == 454
    save(DIRECTORY / "environment-name-tests.json", cases)
    save(DIRECTORY / "environment-name-review.json", {
        "scope": "仅审校调查文字和文书中的人物／神名及典故出处，不宣称逐句重新语义审校",
        "review_document": "docs/dev-tasks/localization/shakespeare-names-2026-10-18/README.md",
        "occurrences": len(rows), "unique_resource_sources": 451, "consumer_cases": len(cases),
        "rows": [{"source_sha256": digest(row["source"]), "origins": [row["origin"]],
                  "decision": "姓名保留；弗罗利泽按全局姓名校订层统一"} for row in rows],
    })


def main():
    changes = read(DIRECTORY / "shakespeare-name-corrections.json")
    review = read(DIRECTORY / "shakespeare-name-review.json")
    terms = {row["id"]: row for row in review["terms"]}
    targets = {row["source"]: row for row in read(ROOT / "translation/sol-full-2026-10-09/translations.json")}
    checked = apply_supplemental([
        {"id": row["original_id"], "source": row["source"], "target": row["previous_target"]}
        for row in changes], changes)
    assert len(checked) == review["changed_dictionary_sources"] == 243
    assets = {(name, sha): text for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())}
    dialogue, _ = source_rows()
    actual_dialogue = {(row["runtime_source"], row["origin"]["scene"], row["origin"]["line"])
                       for row in dialogue}
    cases = []
    for row, checked_row in zip(changes, checked):
        expected = row["previous_target"]
        for term_id in row["term_ids"]:
            term = terms[term_id]
            assert re.search(term["pattern"], row["source"], re.I)
            assert term["previous_name"] in expected
            expected = expected.replace(term["previous_name"], term["name"])
        assert row["target"] == checked_row["target"] == expected
        from prepare_ending_style_followup import apply_styles
        expected = apply_styles([checked_row])[0]["target"]
        assert expected == targets[row["source"]]["target"]
        assert targets[row["source"]]["id"] == row["original_id"]
        for origin in row["origins"]:
            if "asset_sha256" in origin:
                assert (origin["asset"], origin["asset_sha256"]) in assets
            if "scene" in origin:
                assert (row["source"], origin["scene"], origin["line"]) in actual_dialogue or any(
                    raw["source"] == row["source"] and raw["origin"] == origin for raw in dialogue)
            if "governed_alias_file" in origin:
                alias = next(item for item in read(ROOT / origin["governed_alias_file"])
                             if item["id"] == origin["alias_id"])
                prefix = alias.get("runtime_prefix", "")
                suffix = "\n" if alias["id"].startswith("mixed-log-terminal-") else ""
                assert row["target"] == prefix + targets[origin["base_source"]]["target"] + suffix
        cases.append({"id": row["id"], "source": row["source"], "target": expected,
                      "source_sha256": digest(row["source"]), "origins": row["origins"]})
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    changed = {row["source"] for row in changes}
    notice = "<b>Ophelia</b> learns about an event.\n"
    tested = set()
    for row in dialogue:
        source = row["runtime_source"]
        if source not in changed and row["actor"] not in ("quince", "quince2", "katherine"):
            continue
        key = (row["actor"], source)
        if key in tested or source not in targets:
            continue
        tested.add(key)
        target = targets[source]["target"]
        name = short_name(row["actor"], mapping)
        name_target = {"Ghost": "幽灵", "Figure": "戴兜帽的人"}.get(name)
        if name_target is None:
            name_target = targets[name]["target"]
        speaker = "<b>" + name + ":</b> <indent=16%>" + source
        translated = "<b>" + name_target + ":</b> <indent=16%>" + target
        for kind, text, expected in (
            ("box", "<line-height=90%>" + source, "<line-height=90%>" + target),
            ("speaker", speaker, translated),
            ("notice-before", notice + speaker, targets[notice]["target"] + translated),
            ("notice-after", speaker + "</indent>\n" + notice, translated + "</indent>\n" + targets[notice]["target"]),
        ):
            cases.append({"id": "names-" + str(len(tested)) + "-" + kind,
                          "source": text, "target": expected, "origins": [row["origin"]]})
    save(DIRECTORY / "shakespeare-name-tests.json", cases)
    environment_cases(targets)
    print(f"243条姓名覆盖链及别名已核对；生成{len(cases)}项真实词条、对白框、日志和通知组合")


if __name__ == "__main__":
    main()
