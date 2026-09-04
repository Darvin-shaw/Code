"""T3.4 标准对齐与增量/漂移检测核心逻辑（纯标准库）。

输入本体标准映射与三元组，支持：增量合并、版本差异（add/remove）、
受新条款影响的三元组、孤儿引用检查与覆盖统计。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, Set


def apply_delta(mappings: List[dict], delta: dict) -> List[dict]:
    """把标准更新增量合并进现有映射（支持 add/remove 列表）。"""
    result = deepcopy(list(mappings))
    for removed in delta.get("remove", []):
        clause_id = removed.get("clause_id") if isinstance(removed, dict) else removed
        result = [m for m in result if m["clause_id"] != clause_id]
    existing = {m["clause_id"] for m in result}
    for added in delta.get("add", []):
        if added["clause_id"] not in existing:
            result.append(dict(added))
            existing.add(added["clause_id"])
    return result


def compare_maps(previous: List[dict], updated: List[dict]) -> Dict[str, list]:
    """返回条款级差异：新增/删除/未变。"""
    prev = {m["clause_id"] for m in previous}
    curr = {m["clause_id"] for m in updated}
    return {
        "added": sorted(curr - prev),
        "removed": sorted(prev - curr),
        "unchanged_count": len(prev & curr),
    }


def find_affected_triples(triples: Iterable[dict],
                          clause_ids: Set[str]) -> List[dict]:
    """返回 standard_ref 命中新增/变更条款的三元组。"""
    return [
        dict(t) for t in triples
        if t.get("standard_ref") in clause_ids
    ]


def orphan_refs(triples: Iterable[dict], known_clause_ids: Set[str]) -> Set[str]:
    """返回三元组引用但未在标准映射登记的条款。"""
    used = {t.get("standard_ref") for t in triples if t.get("standard_ref")}
    return {clause for clause in used if clause not in known_clause_ids}


def coverage_summary(mappings: List[dict]) -> Dict[str, int | set]:
    docs: Set[str] = set()
    terms: Set[str] = set()
    for mapping in mappings:
        docs.update(mapping.get("internal_docs", []))
        terms.update(mapping.get("ontology_terms", []))
    return {
        "total_mappings": len(mappings),
        "mapped_internal_docs": docs,
        "mapped_ontology_terms": terms,
    }


def build_drift_report(previous: List[dict], updated: List[dict],
                       triples: Iterable[dict]) -> Dict[str, object]:
    """组合版本差异、受影响三元组与更新后覆盖统计，形成漂移报告。"""
    diff = compare_maps(previous, updated)
    new_clause_ids = set(diff["added"])
    affected = find_affected_triples(triples, new_clause_ids)
    affected_docs = {
        doc for mapping in updated if mapping["clause_id"] in new_clause_ids
        for doc in mapping.get("internal_docs", [])
    }
    seen = {_triple_key(t) for t in affected}
    for triple in triples:
        if triple.get("subject_id") in affected_docs and _triple_key(triple) not in seen:
            affected.append(dict(triple))
            seen.add(_triple_key(triple))
    coverage = coverage_summary(updated)
    return {
        "diff": diff,
        "affected_triple_count": len(affected),
        "affected_triples": affected,
        "affected_documents": sorted(affected_docs),
        "coverage": {
            key: sorted(value) if isinstance(value, set) else value
            for key, value in coverage.items()
        },
    }


def _triple_key(triple: dict) -> tuple:
    return (triple.get("subject_id"), triple.get("predicate"), triple.get("object_id"))
