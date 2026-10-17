"""核对王后寝宫斥骂及国王寝宫楼梯语境，生成限定在同一场景内的消费者用例。"""

import re
from prepare_dialogue_log_followup import (
    ROOT, GAME_RESOURCE, SPECIAL_NAMES, read, save, short_name, source_rows,
)
from analyze import read_text_assets


CASES = (
    ("hamlet", "HAMGERT_AftermathNoOne", 3077,
     "You murderous, traitorous woman. You owe my father's honor your life.",
     "你这杀人害命、背信弃义的女人！你得用命来偿还我父亲的名誉。"),
    ("ophelia", "FLAVOR_ClaudiusGrieving", 26500,
     "(He's asleep downstairs, at last.)", "（他终于在楼下睡着了。）"),
)
ASSET_SHA256 = "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a"


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = source_rows()
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}

    def speaker(row):
        name = short_name(row["actor"], mapping)
        target = targets.get(row["runtime_source"])
        if target is None:
            assert row["runtime_source"] == "..."
            target = "..."
        return ("<b>" + name + ":</b> <indent=16%>" + row["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + target)

    tests, audit = [], []
    for actor, scene, line, source, target in CASES:
        scene_rows = [row for row in rows if row["origin"]["asset_sha256"] == ASSET_SHA256
                      and row["origin"]["scene"] == scene]
        row = next(row for row in scene_rows if row["source"] == source and row["actor"] == actor)
        assert row["origin"]["line"] == line and targets[source] == target
        index = scene_rows.index(row)
        context = [speaker(part) for part in scene_rows[max(0, index - 2):index + 3]]
        rendered_source, rendered_target = speaker(row)
        for kind, src, dst in (("leaf", row["runtime_source"], target),
                               ("speaker", rendered_source, rendered_target),
                               ("context", "</indent>\n".join(p[0] for p in context),
                                "</indent>\n".join(p[1] for p in context))):
            tests.append({"id": "royal-chambers-" + actor + "-" + kind,
                          "source": src, "target": dst, "origins": [row["origin"]]})
        audit.append(row)
    script = next(text for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())
                  if name == "scenes" and sha == ASSET_SHA256)
    scene = re.search(r"^\{FLAVOR_ClaudiusGrieving\}.*?(?=^\{[^\r\n{}]+\}\s*$)", script, re.M | re.S).group()
    assert "[Teleport(claudius,limbo)]" in scene and "[Teleport(ophelia,claud_topofstairs)]" in scene
    assert scene.index("[Teleport(ophelia,claud_topofstairs)]") < scene.index(CASES[1][3])
    save(ROOT / "translation/supplemental/royal-chambers-tests.json", tests)
    save(ROOT / "runtime/build/royal-chambers/source-audit.json", audit)
    print("6项斥骂校订、楼下原译及同场景上下文消费者用例已生成")


if __name__ == "__main__":
    main()
