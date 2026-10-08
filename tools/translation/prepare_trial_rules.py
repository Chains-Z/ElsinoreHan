"""将真实试译上下文适配为上游规则配置，不调用模型。"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "translation" / "trial-2026-10-09"


def source_with_speaker(entry: dict) -> str:
    """资料条目可以没有说话人，不能将 None 当字符串拼接。"""
    return (entry.get("name") or "") + " " + entry["message"]


def main() -> None:
    manifest = json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))
    context = json.loads((TRIAL / "context.json").read_text(encoding="utf-8"))
    glossary = json.loads((TRIAL / "glossary.json").read_text(encoding="utf-8"))
    directory = TRIAL / "rules"
    directory.mkdir(exist_ok=True)
    for batch in manifest["batches"]:
        members = [entry for entry in manifest["entries"] if entry["batch"] == batch["id"]]
        if batch["continuous"]:
            facts = context["batches"][batch["id"]]
            background = facts["background"] + "\n只读前文：" + json.dumps(facts["preceding_context"], ensure_ascii=False)
        else:
            background = "以下各项互相独立，不是同一次对话；上下文只供理解，不额外翻译：\n" + "\n".join(
                f"{entry['index'] + 1}. {entry['message']}：{entry['context']}；语体：{entry['register']}"
                for entry in members
            )
        source = "\n".join(source_with_speaker(entry) for entry in members)
        terms = [{"src": item["source"], "dst": item["target"], "info": "本轮暂定译名，跨模型统一，未经过用户确认"}
                 for item in glossary["entries"] if item["source"].lower() in source.lower()]
        rules = {"prompt_dictionary_switch": True, "prompt_dictionary_data": terms,
                 "world_building_switch": True, "world_building_content": background,
                 "characterization_switch": False, "translation_memory_switch": False,
                 "translation_example_switch": False}
        (directory / (batch["id"] + ".json")).write_text(
            json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rules_files": len(manifest["batches"]), "source_entries": len(manifest["entries"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()
