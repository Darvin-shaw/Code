"""T3.3 本体候选三元组审核核心逻辑（纯标准库）。

用于低资源场景下的人工确认闭环：将抽取候选按置信度分流（自动确认/人工审核），
支持 confirmed/rejected 决策、理由与审核人留痕，并输出可人工阅读的审核表。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Tuple


VALID_DECISIONS = {"confirmed", "rejected"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def triple_key(triple: dict) -> Tuple[str, str, str]:
    """三元组唯一键：subject + predicate + object。"""
    return (triple["subject_id"], triple["predicate"], triple["object_id"])


def split_auto_vs_human(candidates: Iterable[dict],
                        auto_threshold: float = 0.9) -> Tuple[List[dict], List[dict]]:
    """按置信度分流：>= auto_threshold 自动确认，其余进入人工审核。"""
    auto: List[dict] = []
    human: List[dict] = []
    for candidate in candidates:
        target = auto if candidate.get("confidence", 0.0) >= auto_threshold else human
        target.append(dict(candidate))
    return auto, human


def apply_policy(candidates: Iterable[dict],
                 confirm_threshold: float = 0.9,
                 reject_threshold: float = 0.4,
                 reviewer: str = "auto-policy") -> Tuple[List[dict], List[dict], List[dict]]:
    """分流策略：高置信自动确认、低置信自动驳回、中间档进入人工审核。"""
    confirmed: List[dict] = []
    rejected: List[dict] = []
    pending: List[dict] = []
    for candidate in candidates:
        confidence = candidate.get("confidence", 0.0)
        if confidence >= confirm_threshold:
            confirmed.append(apply_review(
                candidate, "confirmed",
                reason=f"auto-policy: confidence {confidence} >= {confirm_threshold}",
                reviewer=reviewer))
        elif confidence < reject_threshold:
            rejected.append(apply_review(
                candidate, "rejected",
                reason=f"auto-policy: confidence {confidence} < {reject_threshold}",
                reviewer=reviewer))
        else:
            pending.append(dict(candidate))
    return confirmed, rejected, pending


def apply_review(candidate: dict, decision: str, reason: str = "",
                 reviewer: str = "human-reviewer") -> dict:
    """应用一条人工/自动决策，写入状态与审核痕迹。"""
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision 必须是 {sorted(VALID_DECISIONS)}，收到: {decision}")
    result = dict(candidate)
    result["status"] = decision
    result["reviewed_by"] = reviewer
    result["reviewed_at"] = utc_now()
    result["decision_reason"] = reason
    return result


def render_review_sheet(candidates: Iterable[dict]) -> str:
    """生成 Markdown 审核表，供人工逐条确认。"""
    lines = [
        "# 候选三元组审核表",
        "",
        "| # | subject_id | predicate | object_id | confidence | source | 建议 |",
        "|---|---|---|---|---|---|---|",
    ]
    for idx, candidate in enumerate(candidates, 1):
        suggestion = "自动确认" if candidate.get("confidence", 0) >= 0.9 else "人工审核"
        lines.append(
            f"| {idx} | {candidate['subject_id']} | {candidate['predicate']} "
            f"| {candidate['object_id']} | {candidate.get('confidence', 0)} "
            f"| {candidate.get('source', '')} | {suggestion} |"
        )
    return "\n".join(lines)
