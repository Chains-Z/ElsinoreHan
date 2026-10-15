"""从真实拇指玩笑及相邻对白生成双关校订的消费者回归。"""

from audit_dialect_dialogue import extract_rows
from prepare_dialogue_log_followup import ROOT, SPECIAL_NAMES, read, save, short_name


def main():
    translations = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {row["source"]: row["target"] for row in translations}
    rows, _ = extract_rows(translations)
    row = next(row for row in rows if row["id"] == "p05583-e12b76cd222a")
    assert row["actor"] == "grace"
    assert row["target"] == "连割一小块都不行？那砍根拇指呢？他闲着没事，把拇指往屁股里塞，留<i>一根</i>也够用了吧。"
    assert row["origins"] == [{"asset": "scenes", "asset_sha256": "6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a",
                               "scene": "Mutiny_Note_Reveal", "line": 14907}]
    by_actor_source = {(item["actor"], item["source"]): item for item in rows}
    mapping = {item["origin"]["field"]: item["source"] for item in read(ROOT / "analysis/ui-audit/resource-strings.json")
               if item["origin"].get("asset") == "name_mapping"}

    def speaker(item):
        name = short_name(item["actor"], mapping)
        return ("<b>" + name + ":</b> <indent=16%>" + item["runtime_source"],
                "<b>" + (SPECIAL_NAMES.get(name) or targets[name]) + ":</b> <indent=16%>" + item["target"])

    source, target = speaker(row)
    context = [speaker(by_actor_source[(part["actor"], part["source"])]) for part in row["context"]]
    cases = [{"id": "grace-thumb-" + kind, "source": source, "target": target, "origins": row["origins"]}
             for kind, source, target in (("leaf", row["runtime_source"], row["target"]), ("speaker", source, target),
                 ("context", "</indent>\n".join(part[0] for part in context), "</indent>\n".join(part[1] for part in context)))]
    save(ROOT / "translation/supplemental/grace-thumb-tests.json", cases)
    save(ROOT / "runtime/build/grace-thumb/source-audit.json", row)
    print("3项拇指双关裸句、角色日志及真实相邻语境消费者用例已生成")


if __name__ == "__main__":
    main()
