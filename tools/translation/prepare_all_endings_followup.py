"""核对13个真实结局、编译源与逐段审查记录，导出正文夹具及中英对照阅读稿。"""

import json
import re

from prepare_dialogue_log_followup import GAME_RESOURCE, ROOT, digest, read, read_text_assets, save
from prepare_lead_followup import runtime_source


def paragraph_overrides(entries):
    """后续修订必须绑定精确源与旧译，原始整段审查保留快照。"""
    result = {}
    for entry in entries:
        source = entry["source"]
        if source in result or digest(source) != entry["source_sha256"] or not entry.get("origins"):
            raise ValueError("阅读稿后续修订的源哈希、来源或唯一性不符")
        result[source] = entry
    return result


def apply_reading_followup(reviewed, overrides, used):
    """分别核对资源源句和实际编译源，不能依靠另一变体的译文兜底。"""
    result = dict(reviewed)
    for source_key, target_key in (("source", "resource_target"), ("runtime_source", "target")):
        entry = overrides.get(reviewed[source_key])
        if entry is None:
            continue
        if reviewed[target_key] != entry["previous_target"]:
            raise ValueError("阅读稿后续修订缺少准确旧译")
        result[target_key] = entry["target"]
        used.add(entry["source"])
    return result


def extract_endings():
    assets = {name: (sha, text) for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())
              if name in ("scenes_endings", "endings")}
    source_sha, text = assets["scenes_endings"]
    metadata_sha, metadata = assets["endings"]
    metadata = {row["endingscene"]: row for row in json.loads(metadata)["endings"]}
    markers = list(re.finditer(r'^\{(ENDING_[^\r\n{}]+)\}\s*$', text, re.M))
    assert len(markers) == len(metadata) == 13
    assert {marker[1] for marker in markers} == set(metadata)
    result = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        block = text[marker.end():end]
        paragraphs = []
        for match in re.finditer(r'^\s*(\w+):\s*(?:\{([^}]+)\}\s*)?(".*")\s*$', block, re.M):
            source = json.loads(match[3])
            paragraphs.append({"actor": match[1], "cue": match[2], "source": source,
                               "runtime_source": runtime_source(source),
                               "line": text[:marker.end() + match.start()].count("\n") + 1})
        # 3条无Cue的纯省略号也是实际发言，不能当缺译或漏掉阅读顺序。
        assert sum(1 for _ in re.finditer(r'^\s*\w+\s*:', block, re.M)) == len(paragraphs)
        result.append({"scene": marker[1], "metadata": metadata[marker[1]], "paragraphs": paragraphs})
    return source_sha, metadata_sha, result


def main():
    review = read(ROOT / "translation/supplemental/all-endings-review.json")
    followup_path = ROOT / "translation/supplemental/ending-reading-followup.json"
    followup = read(followup_path) if followup_path.exists() else {"paragraphs": [], "titles": []}
    overrides = paragraph_overrides(followup["paragraphs"])
    # 原审查及阅读反馈先按历史顺序生效，再承接本轮姓名；不改写旧审查快照。
    sources = {row[key] for ending in review["endings"] for row in ending["paragraphs"]
               for key in ("source", "runtime_source")}
    name_overrides = paragraph_overrides([
        row for row in read(ROOT / "translation/supplemental/shakespeare-name-corrections.json")
        if row["source"] in sources])
    used_names = set()
    title_overrides = {entry["ending_id"]: entry for entry in followup["titles"]}
    assert len(title_overrides) == len(followup["titles"])
    used_overrides, used_titles = set(), set()
    source_sha, metadata_sha, actual = extract_endings()
    assert source_sha == review["asset_sha256"]
    assert metadata_sha == review["metadata_sha256"]
    assert len(actual) == len(review["endings"]) == 13
    translations = {row["source"]: row for row in read(
        ROOT / "translation/sol-full-2026-10-09/translations.json")}
    assembly = {row["source"]: row for row in read(ROOT / "analysis/ui-audit/assembly-strings.json")}
    cases, reading = [], ["Elsinore：13个结局完整中英对照正文", "校订候选，包含剧透；按真实结局播放顺序分段，每段中文在上、英文在下。",
                          "原文斜体、粗体以「」标示，仅作阅读提示，游戏内仍保留原强调格式。", ""]
    narrative, pauses, variants, changed = 0, 0, 0, 0
    for extracted, ending in zip(actual, review["endings"]):
        assert extracted["scene"] == ending["scene"]
        assert len(extracted["paragraphs"]) == len(ending["paragraphs"])
        meta = extracted["metadata"]
        title = "舍弃" + translations[meta["sacrifice-what"]]["target"] + "，换取" + translations[meta["sacrifice-for"]]["target"]
        title_revision = title_overrides.get(meta["id"])
        if title_revision is not None:
            assert title_revision["previous_title"] == ending["title"] and title_revision.get("origins")
            assert title_revision["title"] == title
            used_titles.add(meta["id"])
        else:
            assert ending["title"] == title
        assert ending["ending_id"] == meta["id"]
        reading.extend([title, "=" * 32, ""])
        for index, (source, reviewed) in enumerate(zip(extracted["paragraphs"], ending["paragraphs"])):
            for key in ("actor", "cue", "source", "runtime_source", "line"):
                assert source[key] == reviewed[key], (ending["scene"], index, key)
            raw, runtime = source["source"], source["runtime_source"]
            reviewed = apply_reading_followup(reviewed, overrides, used_overrides)
            reviewed = apply_reading_followup(reviewed, name_overrides, used_names)
            assert digest(raw) == reviewed["source_sha256"]
            assert digest(runtime) == reviewed["runtime_source_sha256"]
            if reviewed["nonlexical"]:
                assert raw == runtime == reviewed["target"] == "..." and source["cue"] is None
                pauses += 1
            else:
                narrative += 1
                assert translations[raw]["id"] == reviewed["id"]
                assert translations[raw]["target"] == reviewed["resource_target"]
                assert translations[runtime]["id"] == reviewed["runtime_id"]
                assert translations[runtime]["target"] == reviewed["target"]
                owner = "System.Void GameDataGenerated::Invoke_" + ending["scene"] + "()"
                usages = [usage for usage in assembly[runtime]["usages"] if usage.get("owner") == owner]
                assert usages == reviewed["assembly_usages"] and usages
                changed += reviewed["changed"]
            origin = {"asset": "scenes_endings", "asset_sha256": source_sha,
                      "scene": ending["scene"], "line": source["line"]}
            case_id = ending["scene"] + "-" + str(index + 1)
            cases.append({"id": case_id, "source": runtime, "target": reviewed["target"],
                          "source_sha256": digest(runtime), "origins": [origin]})
            if raw != runtime:
                variants += 1
                cases.append({"id": case_id + "-resource", "source": raw,
                              "target": reviewed["resource_target"], "source_sha256": digest(raw),
                              "origins": [origin]})
            # 中文及其对应的真实编译英文逐段相邻；强调用引号标示，不输出TMP标签。
            content = re.sub(r'<(?:i|b)>(.*?)</(?:i|b)>', r'「\1」', reviewed["target"])
            original = re.sub(r'<(?:i|b)>(.*?)</(?:i|b)>', r'「\1」', runtime)
            reading.extend([content, original, ""])
    assert (narrative, pauses, variants, changed) == (399, 3, 5, 15)
    assert used_overrides == set(overrides) and used_titles == set(title_overrides)
    assert used_names == set(name_overrides)
    assert len(cases) == 407
    save(ROOT / "translation/supplemental/all-endings-tests.json", cases)
    destination = ROOT / "docs/dev-tasks/localization/endings-review-2026-10-18/ending-texts-zh-CN.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(reading), encoding="utf-8", newline="\n")
    print("13结局399段正文、3处省略号与5条编译源变体已核对；生成407项消费者和完整中英对照阅读稿")


if __name__ == "__main__":
    main()
