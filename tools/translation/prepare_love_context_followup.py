"""核对love语境审查及全部归来劝诫，生成真实源消费者与可重读的对照稿。"""

import json
import re

from audit_dialect_dialogue import extract_rows
from export_sol_full import apply_supplemental
from prepare_shakespeare_names_followup import apply_names
from prepare_dialogue_log_followup import (
    DIALOGUE, GAME_RESOURCE, ROOT, SCENE, dialogue_source, digest, read,
    read_text_assets, save, short_name,
)


POST_SCENES = ("POSTEND_Return", "POSTEND_Return_Part2", "remindAboutEndingLost")


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row for row in translations}
    review = read(ROOT / "translation/supplemental/love-context-review.json")
    corrections = read(ROOT / "translation/supplemental/love-context-corrections.json")
    reviewed = {row["source"]: row for row in review["entries"]}
    # 原审查记录保持快照；后续修正只能凭源哈希和准确旧值承接，不用当前输出倒推预期。
    effective_review = review["entries"]
    for filename in ("curtain-call-corrections.json", "ending-marriage-corrections.json"):
        effective_review = apply_supplemental(effective_review, [
            row for row in read(ROOT / "translation/supplemental" / filename)
            if row["source"] in reviewed
        ])
    # 完整结局阅读反馈也可能覆盖love句，例如politician的从政的人；已应用的准确终值不重复覆盖。
    effective = {row["source"]: row for row in effective_review}
    followups = read(ROOT / "translation/supplemental/ending-reading-followup.json")["paragraphs"]
    effective_review = apply_supplemental(effective_review, [
        {**row, "id": effective[row["source"]]["id"]} for row in followups
        if row["source"] in effective and effective[row["source"]]["target"] != row["target"]])
    effective_review = apply_names(effective_review)
    # 覆盖记录ID与实际词条ID不同；派生合同必须校验实际词条的稳定ID。
    corrections = apply_names([{**row, "id": row["original_id"]} for row in corrections])
    actual = {row["source"] for row in translations
              if re.search(review["word_pattern"], row["source"], re.I)}
    assert len(actual) == len(reviewed) == len(review["entries"]) == 431
    assert actual == set(reviewed)
    cases = []
    for index, row in enumerate(effective_review):
        assert digest(row["source"]) == row["source_sha256"] and row["origins"]
        assert targets[row["source"]]["id"] == row["id"]
        assert targets[row["source"]]["target"] == row["target"]
        cases.append({"id": "love-reviewed-" + str(index), "source": row["source"],
                      "target": row["target"], "origins": row["origins"]})
    changed_sources = {row["source"] for row in corrections}
    assert len(changed_sources) == len(corrections) == 25
    for row in corrections:
        assert digest(row["source"]) == row["source_sha256"] and row["origins"]
        assert targets[row["source"]]["target"] == row["target"]

    assets = [(sha, text) for name, sha, text in read_text_assets(GAME_RESOURCE.read_bytes())
              if name == "scenes" and "{POSTEND_Return}" in text]
    assert len(assets) == 1
    asset_sha, text = assets[0]
    markers = list(SCENE.finditer(text))
    reading = ["老国王归来劝诫：完整中英对照", "包含全部互斥分支，不代表一次连续播放。",
               "条件保留原脚本标识；中文在上，英文在下；斜体、粗体以「」作阅读提示。",
               "插件1.5.12补齐原脚本第五次条件缺口：次数为5时也播放原>5分支的两条共用对白。", ""]
    post_review, post_counts = [], {}
    names = {"ghost": "幽灵", "ophelia": "奥菲莉娅"}
    # 幽灵原文有外层斜体和内部强调；逐标签替换，避免单次配对正则漏掉嵌套标签。
    display = lambda value: re.sub(r'</(?:i|b)>', '」', re.sub(r'<(?:i|b)>', '「', value))
    for index, marker in enumerate(markers):
        scene = marker[1]
        if scene not in POST_SCENES:
            continue
        block_end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        block = text[marker.end():block_end]
        reading.extend([scene, "=" * 32, ""])
        count = 0
        for line in block.splitlines():
            match = DIALOGUE.match(line)
            if match:
                source = json.loads('"' + match["text"] + '"')
                actor = match["actor"]
                runtime = dialogue_source(actor, source)
                entry = targets.get(runtime)
                if entry is None:
                    assert source == "...", (scene, source)
                    target = runtime
                else:
                    target = entry["target"]
                origin = {"asset": "scenes", "asset_sha256": asset_sha, "scene": scene}
                row = {"actor": actor, "source": source, "runtime_source": runtime,
                       "runtime_source_sha256": digest(runtime), "target": target,
                       "id": entry["id"] if entry else None, "origins": [origin],
                       "decision": "correct" if runtime in changed_sources else "keep"}
                post_review.append(row)
                count += 1
                cases.append({"id": scene + "-" + str(count), "source": runtime,
                              "target": target, "origins": [origin]})
                reading.extend([names[actor] + "：" + display(target),
                                actor + ": " + display(runtime), ""])
            elif re.match(r"\s*(?:if |elif |else:|endif)", line):
                reading.extend(["【条件：" + line.strip() + "】", ""])
            elif 'call "remindAboutEndingLost"' in line:
                reading.extend(["【插入结局专属提醒，全文见末节】", ""])
            elif "[YesNoPrompt(" in line:
                reading.extend(["【选择：不顾老国王的劝告，返回埃尔西诺？】", ""])
            elif "[AbortToTitle()]" in line:
                reading.extend(["【返回标题画面】", ""])
        post_counts[scene] = count
    assert post_counts == dict(zip(POST_SCENES, (104, 33, 11)))
    assert len(post_review) == 148
    assert len({row["runtime_source"] for row in post_review}) == 132

    dialogue, _ = extract_rows(translations)
    mapping = {row["origin"]["field"]: row["source"]
               for row in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if row["origin"].get("asset") == "name_mapping"}
    notice = "<b>Ophelia</b> learns about an event.\n"
    changed_dialogue = [row for row in dialogue if row["runtime_source"] in changed_sources]
    for index, row in enumerate(changed_dialogue):
        actor = row["actor"]
        name = short_name(actor, mapping)
        target_name = names.get(actor) or targets[name]["target"]
        source = "<b>" + name + ":</b> <indent=16%>" + row["runtime_source"]
        target = "<b>" + target_name + ":</b> <indent=16%>" + targets[row["runtime_source"]]["target"]
        for kind, source, target in (
            ("speaker", source, target),
            ("notice-before", notice + source, targets[notice]["target"] + target),
            ("notice-after", source + "</indent>\n" + notice,
             target + "</indent>\n" + targets[notice]["target"]),
        ):
            cases.append({"id": "love-context-" + str(index) + "-" + kind,
                          "source": source, "target": target, "origins": row["origins"]})
    save(ROOT / "translation/supplemental/love-context-tests.json", cases)
    save(ROOT / "translation/supplemental/post-ending-dialogue-review.json",
         {"date": "2026-10-18", "asset_sha256": asset_sha, "scene_counts": post_counts,
          "reviewed_occurrences": 148, "unique_runtime_sources": 132, "entries": post_review})
    destination = ROOT / "docs/dev-tasks/localization/love-review-2026-10-18/post-ending-texts-zh-CN.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(reading), encoding="utf-8", newline="\n")
    save(ROOT / "runtime/build/love-review/source-audit.json",
         {"love_dictionary_sources": len(actual), "changed_dictionary_sources": len(corrections),
          "post_ending_counts": post_counts, "post_ending_unique_sources": 132,
          "changed_dialogue_actor_sources": len(changed_dialogue), "consumer_cases": len(cases),
          "reading_copy": str(destination.relative_to(ROOT)), "source_asset_sha256": asset_sha})
    print(f"431项love源及148段劝诫已核对；{len(cases)}项真实消费者已生成")


if __name__ == "__main__":
    main()
