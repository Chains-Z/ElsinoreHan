"""从真实奥赛罗故事对白再生时间感受与迟疑问句的消费者回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    expected = {
        "p07165-f8345cba1765": ("time", "othello", 19567,
                               "我感觉她把我留在了那里好多年。我在她的林间漫步，听她唱歌，躺在鲜花铺成的床上。"),
        "p07167-c35c01cc5880": ("intimacy", "ophelia", 19571, "你……你和她……有过肌肤之亲吗？"),
    }
    selected = [row for row in rows if row["id"] in expected]
    assert len(selected) == len(expected)
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"]
               for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + targets[name] + ":</b> <indent=16%>" + item["target"])

    cases = []
    for row in selected:
        label, actor, line, expected_target = expected[row["id"]]
        assert row["actor"] == actor and row["target"] == expected_target
        assert row["origins"] == [{
            "asset": "scenes",
            "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
            "scene": "OTH_OthelloStorytimePrivate1", "line": line,
        }]
        source, target = speaker(row)
        context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
        cases.extend({"id": "othello-story-" + label + "-" + kind,
                      "source": source, "target": target, "origins": row["origins"]}
                     for kind, source, target in (
                         ("leaf", row["runtime_source"], row["target"]), ("speaker", source, target),
                         ("context", "</indent>\n".join(part[0] for part in context),
                          "</indent>\n".join(part[1] for part in context))))
    save(ROOT / "translation/supplemental/othello-story-tests.json", cases)
    save(ROOT / "runtime/build/othello-time/source-audit.json", selected)
    print("6项时间感受、迟疑问句的裸句、角色日志与真实相邻语境用例已生成")


if __name__ == "__main__":
    main()
