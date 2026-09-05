"""M5 T5.2 版本演化回归门（纯逻辑）。

用 Golden 指标对比新/旧版本，指标不退化（或退化在容差内）才允许发布。
"""

from __future__ import annotations

from typing import Dict, List


def regression_gate(old_scores: Dict[str, float],
                    new_scores: Dict[str, float],
                    tolerance: float = 0.05,
                    metrics: List[str] | None = None) -> bool:
    """True 表示新版本可发布；任一受控指标退化超过容差则 False。"""
    controlled = metrics or sorted(set(old_scores) & set(new_scores))
    for metric in controlled:
        if old_scores.get(metric, 0.0) - new_scores.get(metric, 0.0) > tolerance:
            return False
    return True


def evolution_report(old_version: str,
                     new_version: str,
                     old_scores: Dict[str, float],
                     new_scores: Dict[str, float],
                     changes: List[str],
                     tolerance: float = 0.05) -> Dict[str, object]:
    """生成版本演化摘要：变更、指标对比、回归门结论。"""
    passed = regression_gate(old_scores, new_scores, tolerance=tolerance)
    deltas = {
        metric: round(new_scores.get(metric, 0.0) - old_scores.get(metric, 0.0), 4)
        for metric in sorted(set(old_scores) | set(new_scores))
    }
    return {
        "old_version": old_version,
        "new_version": new_version,
        "changes": changes,
        "old_scores": old_scores,
        "new_scores": new_scores,
        "deltas": deltas,
        "tolerance": tolerance,
        "passed": passed,
    }
