"""一次性迁移已核实的格式关系；日常导出只读取规范译文与派生合同。"""

import argparse
from collections import defaultdict, deque

from audit_dialect_dialogue import extract_rows
from audit_source_variants import collect_pairs
from export_sol_full import apply_supplemental
from prepare_dialogue_log_followup import ROOT, read, save
from prepare_lead_followup import runtime_source
from source_variant_generation import digest, render_variants, unwrap, wrap


DIRECTORY = ROOT / "translation/supplemental"
CANONICAL = DIRECTORY / "canonical-variant-translations.json"
MANIFEST = DIRECTORY / "generated-variant-bindings.json"


def collect_relationships(rows):
    by_source = {row["source"]: row for row in rows}
    dialogue, _ = extract_rows(rows)
    compiled = {row["source"] for row in read(ROOT / "analysis/ui-audit/assembly-strings.json")}
    pairs, exclusions, missing = collect_pairs(rows, dialogue, compiled)
    if missing:
        raise ValueError("真实编译源缺条，不能迁移")
    active = {row["runtime_source"] for row in dialogue if row["runtime_source"] in compiled}
    relationships, exceptions = [], []
    for row in pairs:
        variant = row["runtime_source"]
        base = next(source for source in (row["source"], row["source"].strip()) if source in by_source)
        prefix, suffix = ("<i>", "</i>") if row["actor"] == "ghost" else ("", "")
        edge = {"kind": "dialogue", "base": base, "variant": variant,
                "resource_source": row["source"], "resource_lookup_trimmed": row["resource_lookup_trimmed"],
                "actor": row["actor"], "prefix": prefix, "suffix": suffix, "origins": row["origins"]}
        if base in active and by_source[variant]["target"] != wrap(by_source[base]["target"], prefix, suffix):
            exceptions.append({**edge, "reason": "裸源同时是其它角色的实际运行对白，当前语境答复不同，分别维护规范译文"})
        else:
            relationships.append(edge)
    for row in read(ROOT / "analysis/ui-audit/resource-strings.json"):
        origin = row["origin"]
        if (origin.get("asset"), origin.get("field")) not in {
                ("leads", "text"), ("bios", "text"), ("closeups", "text"),
                ("information", "long"), ("information", "short")}:
            continue
        base, variant = row["source"], runtime_source(row["source"])
        if base != variant and base in by_source and variant in by_source:
            active.add(variant)
            relationships.append({"kind": "resource", "base": base, "variant": variant,
                                  "prefix": "", "suffix": "", "origins": [origin]})
    explicit_count = 0
    for path in sorted(DIRECTORY.glob("*.json")):
        if not any(word in path.name for word in ("alias", "translation")) or path == CANONICAL:
            continue
        entries = read(path)
        if not isinstance(entries, list):
            continue
        for row in entries:
            if not isinstance(row, dict) or not ("existing_source" in row or "base_source" in row):
                continue
            base = row.get("existing_source", row.get("base_source"))
            variant = row["source"]
            prefix = row.get("runtime_prefix", "")
            suffix = "\n" if "base_source" in row else ""
            if by_source[variant]["target"] != wrap(by_source[base]["target"], prefix, suffix):
                raise ValueError("显式别名当前已失配，请先校订")
            explicit_count += 1
            relationships.append({"kind": "explicit", "base": base, "variant": variant,
                                  "prefix": prefix, "suffix": suffix,
                                  "base_sha256": digest(base), "variant_sha256": digest(variant),
                                  "origins": [{"governed_alias_file": path.relative_to(ROOT).as_posix(),
                                               "alias_id": row["id"]}, *row["origins"]]})
    # 相同关系保留一种最直接的来源；实际资源复核仍由独立审查执行。
    unique = {}
    for edge in relationships:
        unique.setdefault((edge["base"], edge["variant"], edge["prefix"], edge["suffix"]), edge)
    return list(unique.values()), exceptions, active, {
        "dialogue_pairs": len(pairs), "explicit_alias_contracts": explicit_count,
        "exclusions": exclusions,
    }


def migrate(rows, relationships, exceptions, active):
    by_source = {row["source"]: row for row in rows}
    graph = defaultdict(list)
    for edge in relationships:
        graph[edge["base"]].append((edge["variant"], edge, True))
        graph[edge["variant"]].append((edge["base"], edge, False))
    for edge in exceptions:
        graph[edge["base"]]
        graph[edge["variant"]]
    canonical, bindings, visited = [], [], set()
    for first in sorted(graph):
        if first in visited:
            continue
        component, tiers = [], {first: 0}
        queue = deque([first])
        while queue:
            source = queue.popleft()
            component.append(source)
            for adjacent, edge, forward in graph[source]:
                tier = tiers[source] + (int(bool(edge["prefix"] or edge["suffix"])) * (1 if forward else -1))
                if adjacent in tiers:
                    if tiers[adjacent] != tier:
                        raise ValueError("格式关系存在不一致环路")
                else:
                    tiers[adjacent] = tier
                    queue.append(adjacent)
        visited.update(component)
        root = min(component, key=lambda source: (tiers[source], len(source), source))
        trusted = sorted(set(component) & active, key=lambda source: (tiers[source], len(source), source))
        authority = trusted[0] if trusted else root
        values = {authority: by_source[authority]["target"]}
        queue = deque([authority])
        while queue:
            source = queue.popleft()
            for adjacent, edge, forward in graph[source]:
                value = (wrap if forward else unwrap)(values[source], edge["prefix"], edge["suffix"])
                if adjacent in values:
                    if values[adjacent] != value:
                        raise ValueError("格式关系的中文推导存在冲突")
                else:
                    values[adjacent] = value
                    queue.append(adjacent)
        conflicts = [source for source in trusted if values[source] != by_source[source]["target"]]
        if conflicts:
            raise ValueError("迁移将改写已存在的实际运行译文，请先登记语境例外：" + repr(conflicts[0]))
        formats = {root: ("", "")}
        queue = deque([root])
        while queue:
            source = queue.popleft()
            prefix, suffix = formats[source]
            for adjacent, edge, forward in graph[source]:
                if forward:
                    form = (edge["prefix"] + prefix, suffix + edge["suffix"])
                else:
                    form = (unwrap(prefix, edge["prefix"], ""), unwrap(suffix, "", edge["suffix"]))
                if adjacent in formats:
                    if formats[adjacent] != form:
                        raise ValueError("相同源对应不同格式路径")
                else:
                    formats[adjacent] = form
                    queue.append(adjacent)
        identifier = "canonical-" + digest(root)[:16]
        origins = [{"translation_id": by_source[authority]["id"], "source_sha256": digest(authority),
                    "note": "复用迁移前已审运行译文；不重新翻译正文"}]
        canonical.append({"id": identifier, "source": root, "source_sha256": digest(root),
                          "target": values[root], "migration_authority_source": authority, "origins": origins})
        for source in sorted(component):
            prefix, suffix = formats[source]
            if wrap(values[root], prefix, suffix) != values[source]:
                raise ValueError("规范译文不能准确重建迁移值")
            bindings.append({"source": source, "source_sha256": digest(source),
                             "original_id": by_source[source]["id"],
                             "previous_target": by_source[source]["target"],
                             "canonical_id": identifier, "prefix": prefix, "suffix": suffix})
    manifest = {"schema_version": 1, "bindings": bindings, "relationships": relationships,
                "context_exceptions": exceptions}
    result = render_variants(rows, canonical, manifest)
    return canonical, manifest, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initialize", action="store_true", help="仅第一次迁移使用，拒绝覆盖已存在的规范译文")
    args = parser.parse_args()
    if not args.initialize or CANONICAL.exists() or MANIFEST.exists():
        raise SystemExit("日常导出不运行迁移；初始化必须显式指定且不能覆盖已有规范译文")
    rows = read(ROOT / "translation/sol-full-2026-10-09/translations.json")
    titles = read(DIRECTORY / "playmaster-title-corrections.json")
    rows = apply_supplemental(rows, titles)
    relationships, exceptions, active, summary = collect_relationships(rows)
    canonical, manifest, result = migrate(rows, relationships, exceptions, active)
    manifest["migration_summary"] = summary
    save(CANONICAL, canonical)
    save(MANIFEST, manifest)
    save(ROOT / "runtime/build/variant-generation/expected-translations.json", result)
    print({"canonical_translations": len(canonical), "bindings": len(manifest["bindings"]),
           "relationships": len(relationships), "context_exceptions": len(exceptions), **summary})


if __name__ == "__main__":
    main()
