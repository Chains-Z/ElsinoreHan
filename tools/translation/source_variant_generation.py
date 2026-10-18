"""从单一审定译文派生格式变体；旧阶段译文仅作为不可变的迁移校验基线。"""

import hashlib

from prepare_lead_followup import runtime_source
from run_sol_full import validate


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def wrap(text, prefix, suffix):
    return prefix + text + suffix


def unwrap(text, prefix, suffix):
    """只去除指定的一层编译格式，不吞掉原有句内强调。"""
    if not text.startswith(prefix) or not text.endswith(suffix):
        raise ValueError("派生格式缺少对应的前后封套")
    end = len(text) - len(suffix) if suffix else len(text)
    if end < len(prefix):
        raise ValueError("派生格式前后封套重叠")
    return text[len(prefix):end]


def validate_relationship(edge):
    """推导规则只适用于真实编译路径；显式空白别名按原合同绑定准确源。"""
    base, variant = edge["base"], edge["variant"]
    if not edge.get("origins"):
        raise ValueError("派生关系缺少真实来源")
    kind = edge["kind"]
    if kind == "dialogue":
        prefix, suffix = ("<i>", "</i>") if edge["actor"] == "ghost" else ("", "")
        if variant != wrap(runtime_source(edge["resource_source"]), prefix, suffix):
            raise ValueError("对白源不符合实际编译规则")
        if base != edge["resource_source"] and not (
                edge.get("resource_lookup_trimmed") and base == edge["resource_source"].strip()):
            raise ValueError("对白资源查找源不符")
    elif kind == "resource":
        prefix, suffix = "", ""
        if variant != runtime_source(base):
            raise ValueError("资源源不符合实际编译规则")
    elif kind == "explicit":
        prefix, suffix = edge["prefix"], edge["suffix"]
        # 部分历史精确别名来自资源空白差异，不能按任意空白正则泛化。
        for field, text in (("base_sha256", base), ("variant_sha256", variant)):
            if edge.get(field) != digest(text):
                raise ValueError("显式运行别名的源哈希不符")
        if prefix not in ("", "<line-height=90%>") or suffix not in ("", "\n"):
            raise ValueError("未知显式运行封套")
    else:
        raise ValueError("未知派生关系类型")
    if (edge["prefix"], edge["suffix"]) != (prefix, suffix):
        raise ValueError("派生目标格式与来源规则不符")


def render_variants(rows, canonical, manifest):
    """先核对旧覆盖链，再只从规范译文生成输出，拒绝单边更新和重复绑定。"""
    if manifest.get("schema_version") != 1:
        raise ValueError("未知派生合同版本")
    by_source = {row["source"]: row for row in rows}
    if len(by_source) != len(rows):
        raise ValueError("输入词表有重复源")
    central = {}
    for row in canonical:
        if row["id"] in central or not row.get("origins") or digest(row["source"]) != row["source_sha256"]:
            raise ValueError("规范译文ID、来源或源哈希不完整")
        central[row["id"]] = row
    bindings = {}
    output = [dict(row) for row in rows]
    emitted = {row["source"]: row for row in output}
    for binding in manifest["bindings"]:
        source = binding["source"]
        if source in bindings:
            raise ValueError("同一输出键绑定了多份规范译文")
        bindings[source] = binding
        old = by_source.get(source)
        if (old is None or old["id"] != binding["original_id"]
                or digest(source) != binding["source_sha256"]
                or old["target"] != binding["previous_target"]):
            raise ValueError("历史词条发生单边变化，请改规范译文而不是旧阶段目标")
        if binding["canonical_id"] not in central:
            raise ValueError("派生键引用的规范译文不存在")
        target = wrap(central[binding["canonical_id"]]["target"], binding["prefix"], binding["suffix"])
        candidate = {"id": old["id"], "source": source}
        if validate([candidate], {"translations": [{"id": old["id"], "target": target}]}):
            raise ValueError("派生译文损坏原始格式或占位符")
        emitted[source]["target"] = target
        emitted[source]["canonical_translation_id"] = binding["canonical_id"]
    if set(central) != {binding["canonical_id"] for binding in bindings.values()}:
        raise ValueError("存在未使用的规范译文")
    for edge in manifest["relationships"]:
        validate_relationship(edge)
        if edge["base"] not in bindings or edge["variant"] not in bindings:
            raise ValueError("派生关系缺少输出键")
        expected = wrap(emitted[edge["base"]]["target"], edge["prefix"], edge["suffix"])
        if emitted[edge["variant"]]["target"] != expected:
            raise ValueError("派生关系的最终译文失配")
    for exception in manifest["context_exceptions"]:
        validate_relationship(exception)
        if not exception.get("reason") or exception["base"] not in bindings or exception["variant"] not in bindings:
            raise ValueError("语境例外缺少理由或独立绑定")
        if bindings[exception["base"]]["canonical_id"] == bindings[exception["variant"]]["canonical_id"]:
            raise ValueError("语境例外被错误地合并")
    return output


def project_subset(rows, canonical, manifest):
    """历史审查只含部分词条，仍按同一合同校验旧译后派生，不另存一套译文。"""
    sources = {row["source"] for row in rows}
    bindings = [row for row in manifest["bindings"] if row["source"] in sources]
    used = {row["canonical_id"] for row in bindings}
    selected = {**manifest, "bindings": bindings}
    for key in ("relationships", "context_exceptions"):
        selected[key] = [row for row in manifest[key] if {row["base"], row["variant"]} <= sources]
    return render_variants(rows, [row for row in canonical if row["id"] in used], selected)


def reading_overrides(sources, canonical, manifest):
    """阅读稿复用历史旧译的严格校验入口；最终文字只取规范译文。"""
    central = {row["id"]: row for row in canonical}
    return [{"source": row["source"], "source_sha256": row["source_sha256"],
             "previous_target": row["previous_target"],
             "target": wrap(central[row["canonical_id"]]["target"], row["prefix"], row["suffix"]),
             "origins": central[row["canonical_id"]]["origins"]}
            for row in manifest["bindings"] if row["source"] in sources]
