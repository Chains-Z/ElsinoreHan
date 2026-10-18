"""从真实女王结局核对完整独白，为逐段校订生成离线消费者夹具。"""

import json
import re

from prepare_dialogue_log_followup import GAME_RESOURCE, ROOT, digest, read, read_text_assets, save


def main():
    review = read(ROOT / "translation/supplemental/queen-ending-review.json")
    asset_hash, text = next((sha, text) for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())
                           if name == "scenes_endings")
    assert asset_hash == review["asset_sha256"]
    scene = text.split("{ENDING_Queen}", 1)[1].split("increment numberEndingsBurned", 1)[0]
    actual = [(match[1], json.loads(match[2])) for match in re.finditer(
        r'^ophelia:\s*\{([^}]+)\}\s*(".*")$', scene, re.M)]
    assert len(actual) == review["dialogue_count"] == 33
    assert sum(row["changed"] for row in review["paragraphs"]) == review["changed_count"] == 6
    translations = {row["source"]: row for row in read(
        ROOT / "translation/sol-full-2026-10-09/translations.json")}
    cases = []
    for (cue, source), row in zip(actual, review["paragraphs"]):
        assert (cue, source) == (row["cue"], row["source"])
        assert digest(source) == row["source_sha256"]
        assert translations[source]["id"] == row["id"]
        assert translations[source]["target"] == row["target"]
        assert row["changed"] == (row["previous_target"] != row["target"])
        # 结局为EndingSceneUI逐段正文；不伪造普通对话框或日志封套作为运行变体。
        cases.append({"id": "queen-ending-" + cue, "source": source, "target": row["target"],
                      "source_sha256": row["source_sha256"], "origins": [row["origin"]]})
    save(ROOT / "translation/supplemental/queen-ending-tests.json", cases)
    print("33项真实女王结局正文消费者夹具已生成；6段修改、27段保持")


if __name__ == "__main__":
    main()
