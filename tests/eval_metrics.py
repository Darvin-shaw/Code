"""M5 T5.1 离线评测指标（纯函数）。

支撑指标：证据召回/精确、反证违规、溯源完整度、单题聚合分。
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Set


def evidence_recall(retrieved: Set[str], required: Set[str]) -> float:
    if not required:
        return 1.0
    return len(retrieved & required) / len(required)


def evidence_precision(retrieved: Set[str], required: Set[str]) -> float:
    if not retrieved:
        return 0.0
    return len(retrieved & required) / len(retrieved)


def forbidden_violations(retrieved: Iterable[str],
                         forbidden: Iterable[str]) -> List[str]:
    return sorted(set(retrieved) & set(forbidden))


def traceability_complete(used_evidence: Set[str], assertions: List) -> bool:
    """每条断言都至少绑定一条证据。"""
    if not assertions:
        return False
    if all(isinstance(item, str) for item in assertions):
        return len(used_evidence) >= len(assertions)
    return all(bool(ids) for ids in assertions)


def score_case(required: Iterable[str],
               forbidden: Iterable[str],
               retrieved: Iterable[str],
               assertions_evidence: Dict[int, List[str]]) -> Dict[str, object]:
    required_set = set(required)
    retrieved_set = set(retrieved)
    used = {eid for ids in assertions_evidence.values() for eid in ids}
    per_assertion = list(assertions_evidence.values())
    return {
        "recall": evidence_recall(retrieved_set, required_set),
        "precision": evidence_precision(retrieved_set, required_set),
        "forbidden_violations": forbidden_violations(retrieved_set, forbidden),
        "traceable": traceability_complete(used, per_assertion),
    }
