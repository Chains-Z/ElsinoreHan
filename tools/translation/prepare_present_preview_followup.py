"""给真实分享首句白名单补齐编译破折号变体，保留原有来源与范围。"""

import json
import re

from prepare_dialogue_log_followup import ROOT, read, save
from prepare_lead_followup import runtime_source


def main():
    audit = read(ROOT / "analysis/ui-audit/notification-source-audit.json")
    sources = audit["share_display_sources"]
    full = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    targets = {r["source"]: r["target"] for r in full}
    allowed = {r["source"] for r in sources}
    allowed.update(runtime_source(r["source"]) for r in sources)
    changed = {runtime_source(r["source"]) for r in sources if runtime_source(r["source"]) != r["source"]}
    rules_path = ROOT / "translation/supplemental/notification-ui-rules.json"
    rules = read(rules_path)
    rule = next(r for r in rules if r["id"] == "ui-rule-present-first-dialogue-quoted")
    previous = re.compile(rule["pattern"].replace("(?<body>", "(?P<body>").replace(r"\z$", r"\Z"))
    missing = [s for s in sorted(allowed) if not previous.fullmatch('"' + s + '"')]
    rule["pattern"] = '^"(?<body>(?:' + "|".join(re.escape(s) for s in sorted(allowed, key=lambda s: (-len(s), s))) + '))"\\z$'
    rule["runtime_first_line_revision"] = 1
    origin = "analysis/ui-audit/present-preview-source-audit.json"
    if origin not in rule["origins"]:
        rule["origins"].append(origin)
        rule["note"] += "；原始首句及Compiler九步破折号运行变体均接受，不泛化任意引号正文"
    save(rules_path, rules)
    cases = []
    for index, row in enumerate(sources):
        raw, runtime = row["source"], runtime_source(row["source"])
        for kind, source in (("raw", raw), ("runtime", runtime)):
            target = targets.get(source, targets.get(raw))
            if target is None:
                raise ValueError("已审核分享首句缺少正文：" + source)
            cases.append({"id": "present-preview-" + kind + "-" + str(index),
                          "source": '"' + source + '"', "target": "“" + target + "”"})
    cases.append({"id": "present-preview-unknown", "source": '"Unknown internal preview"', "target": None})
    build = ROOT / "runtime/build/present-preview-followup"
    build.mkdir(parents=True, exist_ok=True)
    save(build / "consumer-tests.json", cases)
    # 仓库保留变体缺口和未知拒绝例，全量派生用例可再生。
    save(ROOT / "translation/supplemental/present-preview-followup-tests.json",
         [r for r in cases if r["target"] is None or r["source"][1:-1] in changed])
    print(json.dumps({"raw_sources": len(sources), "allowed_sources": len(allowed),
                      "new_runtime_sources": len(missing), "cases": len(cases)}))


if __name__ == "__main__":
    main()
