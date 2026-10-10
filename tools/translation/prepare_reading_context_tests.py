"""生成本轮宫廷称号与对白语境的定向真实消费者用例。"""

import json
from prepare_dialogue_log_followup import ROOT, read, save


def main():
    directory = ROOT / "translation/supplemental"
    changes = (read(directory / "court-title-corrections.json") + read(directory / "dialogue-context-corrections.json")
               + read(directory / "reading-document-corrections.json"))
    cases = [{"id": row["id"] + "-leaf", "source": row["source"], "target": row["target"], "origins": row["origins"]}
             for row in changes]
    for row in changes:
        if not row["id"].startswith("dialogue-context-"):
            continue
        speakers = {"p02686-3308fc1fb0fd": ("Hamlet", "哈姆雷特"),
                    "p02687-d1e4494f09eb": ("Hamlet", "哈姆雷特"),
                    "p04724-17500c24bf52": ("Quince", "奎因斯"),
                    "p01429-cfac3c4184a6": ("Quince", "奎因斯"),
                    "p11946-78df2794f513": ("Quince", "奎因斯"),
                    "p04044-2faad0554345": ("Polonius", "波洛涅斯"),
                    "p04047-b18e9b908b5c": ("Polonius", "波洛涅斯"),
                    "p09190-4371d46d4f86": ("Brit", "布莉特"),
                    "p00287-446b0d6707f4": ("Ophelia", "奥菲莉娅")}
        name, target_name = speakers[row["original_id"]]
        cases.append({"id": row["id"] + "-speaker",
                      "source": "<b>" + name + ":</b> <indent=16%>" + row["source"],
                      "target": "<b>" + target_name + ":</b> <indent=16%>" + row["target"]})
    adjacent = [next(r for r in changes if r["original_id"] == identifier)
                for identifier in ("p02686-3308fc1fb0fd", "p02687-d1e4494f09eb")]
    cases.append({"id": "hamlet-context-pair",
                  "source": "<b>Hamlet:</b> <indent=16%>" + "\n".join(r["source"] for r in adjacent),
                  "target": "<b>哈姆雷特:</b> <indent=16%>" + "\n".join(r["target"] for r in adjacent)})
    save(directory / "reading-context-tests.json", cases)
    print(json.dumps({"corrections": len(changes), "cases": len(cases)}))


if __name__ == "__main__":
    main()
