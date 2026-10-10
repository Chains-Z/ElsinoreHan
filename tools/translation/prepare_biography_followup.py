"""从全部真实人物简介资源生成精确运行别名、有限组合规则与可复现夹具。"""

import argparse
import base64
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

from prepare_lead_followup import runtime_source

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "translation/supplemental"
sys.path.insert(0, str(ROOT / "analysis"))
from analyze import normalize, read_json, read_text_assets


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def extract_resources(path):
    """只读取资源载荷；保留行内换行和空白，不修改游戏资源。"""
    data = path.read_bytes()
    resources = []
    for name, asset_sha, text in read_text_assets(data):
        if name != "bios":
            continue
        value = read_json(text)
        actors = []
        for actor_index, actor in enumerate(value["list"]):
            lines = []
            for line_index, line in enumerate(actor["lines"]):
                origin = {"file": path.name, "asset": name, "asset_sha256": asset_sha,
                          "json_path": f"$.list[{actor_index}].lines[{line_index}].text",
                          "field": "text", "actor": actor["id"], "record_id": line["id"]}
                lines.append({"line_index": line_index, "line_id": line["id"], "source": line["text"],
                              "source_sha256": digest(line["text"]), "active": line.get("active", []),
                              "origin": origin})
            actors.append({"actor": actor["id"], "slug": actor["slug"], "subtitle": actor["subtitle"], "lines": lines})
        resources.append({"asset": name, "asset_sha256": asset_sha, "actors": actors})
    if not resources:
        raise ValueError("未发现真实bios资源")
    return resources, hashlib.sha256(data).hexdigest()


def resolve_original(raw, runtime, translations):
    """规范化只用于唯一定位既有条目；运行别名仍保持精确源字节。"""
    by_source = {row["source"]: row for row in translations}
    original = by_source.get(runtime) or by_source.get(raw) or by_source.get(raw.strip())
    if original is None:
        candidates = [row for row in translations if normalize(row["source"]) == normalize(raw)]
        if len(candidates) != 1:
            raise ValueError("简介空白变体缺少唯一原条目：" + raw[:80])
        original = candidates[0]
    return original


def build(resources, translations):
    """限定同角色真实资源行及保序子集，完整行内段落保持为单个原子。"""
    by_source = {row["source"]: row for row in translations}
    aliases, groups, cases, rules = {}, {}, [], []
    ordered_count = 0
    for resource_index, resource in enumerate(resources):
        for actor in resource["actors"]:
            group = groups.setdefault(actor["actor"], {"actor": actor["actor"], "versions": [], "atoms": {}})
            lines = []
            for line in actor["lines"]:
                raw = line["source"]
                if digest(raw) != line["source_sha256"]:
                    raise ValueError("简介资源源哈希不符")
                source = runtime_source(raw)
                original = resolve_original(raw, source, translations)
                target = original["target"]
                current = {**line, "source": source, "raw_source": raw, "target": target,
                           "translation_id": original["id"]}
                lines.append(current)
                group["atoms"][source] = current
                if source not in by_source:
                    alias = {"id": "ui-bio-runtime-" + digest(source)[:16], "source": source, "target": target,
                             "source_sha256": digest(source), "origins": [line["origin"], "runtime/build/document-scroll/biography-il.json"],
                             "existing_id": original["id"], "existing_source": original["source"],
                             "existing_source_sha256": digest(original["source"]), "existing_target_sha256": digest(target),
                             "provenance": "真实人物简介编译破折号或行内空白变体，逐字复用既有译文"}
                    previous = aliases.get(source)
                    if previous and previous["target"] != target:
                        raise ValueError("人物简介运行别名目标冲突")
                    if previous:
                        previous["origins"].append(line["origin"])
                    else:
                        aliases[source] = alias
            group["versions"].append({"asset_sha256": resource["asset_sha256"], "lines": lines})
            for size in range(1, len(lines) + 1):
                for indices in itertools.combinations(range(len(lines)), size):
                    ordered_count += 1
                    parts = [lines[index] for index in indices]
                    for variant, prefix in (("bare", ""), ("height", "<line-height=90%>")):
                        source = prefix + "\n\n".join(row["source"] for row in parts)
                        target = prefix + "\n\n".join(row["target"] for row in parts)
                        cases.append({"id": f"bio-{resource_index}-{actor['actor']}-{'-'.join(map(str, indices))}-{variant}",
                                      "source": source, "source_sha256": digest(source), "target": target,
                                      "target_sha256": digest(target), "origins": [row["origin"] for row in parts],
                                      "verification_level": "真实资源保序子集，不代表当前存档已解锁这些人物资料"})
    for actor, group in sorted(groups.items()):
        atoms = sorted(group["atoms"], key=lambda source: (-len(source), source))
        if max(len(version["lines"]) for version in group["versions"]) < 2:
            continue
        union = "(?:" + "|".join(re.escape(source) for source in atoms) + ")"
        # 前瞻按各资源原顺序约束；尾分隔符由正文消费式拒绝，不能接受重复/倒序行。
        sequences = []
        for version in group["versions"]:
            sequence = "".join("(?:" + re.escape(row["source"]) + r"(?:\n\n|(?=\z)))?" for row in version["lines"])
            if sequence not in sequences:
                sequences.append(sequence)
        guard = "(?=(?:" + "|".join(sequences) + r")\z)"
        pattern = (r"^(?<prefix_i><line-height=90%>)?" + guard + r"(?<first>" + union
                   + r")(?<separator_i>\n\n)(?<rest>" + union + r"(?:\n\n" + union + r")*)\z$")
        rules.append({"id": "ui-rule-biography-paragraphs-" + actor, "priority": 86,
                      "pattern": pattern, "replacement": "${prefix_i}${first}${separator_i}${rest}",
                      "origins": ["runtime/build/document-scroll/biography-il.json", *[version["lines"][0]["origin"] for version in group["versions"]]],
                      "note": "只拆同角色资源的保序简介组合；完整行内段落不拆，未知/重复/倒序行失败，保留行高和双LF"})
        selected = max(reversed(group["versions"]), key=lambda version: len(version["lines"]))["lines"]
        for where, parts in (("front", [None, *selected]), ("middle", [selected[0], None, *selected[1:]]), ("back", [*selected, None])):
            source = "\n\n".join(row["source"] if row else "Unknown biography paragraph sentinel" for row in parts)
            cases.append({"id": "bio-unknown-" + actor + "-" + where, "source": source, "target": None,
                          "source_sha256": digest(source), "target_sha256": None,
                          "origins": ["拒绝未知人物资料段落的格式回归"]})
    return list(aliases.values()), rules, cases, groups, ordered_count


def write_runtime_cases(path, groups):
    """真实组件重放使用裸源及带行高期望，末列绑定真实头像角色枚举。"""
    selected = []
    for actor, group in sorted(groups.items()):
        lines = max(reversed(group["versions"]), key=lambda version: len(version["lines"]))["lines"]
        selected.append(("bio-runtime-all-" + actor, actor, lines))
    hamlet = {row["line_id"]: row for version in groups["hamlet"]["versions"] for row in version["lines"]}
    selected.append(("bio-runtime-screenshot-hamlet", "hamlet", [hamlet["initial"], hamlet["hamlet2"]]))
    encode = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(case_id + "\t" + encode("\n\n".join(row["source"] for row in lines)) + "\t"
                            + encode("<line-height=90%>" + "\n\n".join(row["target"] for row in lines)) + "\t" + actor + "\n"
                            for case_id, actor, lines in selected), encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, default=Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/resources.assets"))
    parser.add_argument("--runtime-cases", type=Path, default=ROOT / "runtime/build/biography-followup/runtime-cases.tsv")
    args = parser.parse_args()
    translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
    # 重跑时去掉本生成器的既有别名，确保派生条目不会反过来成为自己的治理来源。
    translations = [row for row in translations if not row["id"].startswith("ui-bio-runtime-")]
    resources, resources_sha = extract_resources(args.resources)
    aliases, rules, cases, groups, ordered_count = build(resources, translations)
    for filename, value in (("bio-runtime-aliases.json", aliases), ("biography-followup-rules.json", rules)):
        save(OUT / filename, value)
    save(ROOT / "runtime/build/biography-followup/consumer-tests.json", cases)
    save(ROOT / "runtime/build/biography-followup/manifest.json", groups)
    write_runtime_cases(args.runtime_cases, groups)
    summary = {"resources_sha256": resources_sha, "assets": len(resources), "actors": len(groups),
               "line_occurrences": sum(len(actor["lines"]) for resource in resources for actor in resource["actors"]),
               "unique_sources": len({row["source"] for group in groups.values() for row in group["atoms"].values()}),
               "ordered_subsets": ordered_count, "aliases": len(aliases), "rules": len(rules), "cases": len(cases),
               "runtime_cases": len(groups) + 1,
               "limits": ["穷举真实资源全部保序非空子集；不声明所有剧情进度可同时成立", "源变体只复用既有目标；未重新翻译人物简介"]}
    save(ROOT / "runtime/evidence/biography-source-audit.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
