"""M4 T4.4 决策溯源报告（Markdown + Mermaid）。

组合证据链工作流输出，生成面向评审/客户的可读报告。
"""

from __future__ import annotations

from typing import Dict, List

from mcp_servers.decision_trace_server.evidence_workflow import run_evidence_workflow


def render_full_report(question: str,
                       assertions: List[dict],
                       evidence: List[dict]) -> str:
    """渲染完整决策报告文本。"""
    result = run_evidence_workflow(question, assertions, evidence)
    lines = [
        "# 决策报告",
        "",
        f"## 问题",
        "",
        question,
        "",
        "## 结论与依据",
        "",
    ]
    lines.append(result["markdown"])
    lines.extend(["", "## 证据清单"])
    for item in evidence:
        lines.append(
            f"- `{item['evidence_id']}`（{item.get('role', 'support')}）："
            f"{item['source_file']}"
            + (f"：{item['quote']}" if item.get("quote") else ""))
    lines.extend(["", "## 决策图", "", "```mermaid", result["mermaid"], "```", ""])
    if not result["traceable"]:
        lines.append("> 状态：证据不足/未通过审计")
        for issue in result["issues"]:
            lines.append(f"> - {issue}")
        lines.append("")
    else:
        lines.append("> 状态：可溯源")
        lines.append("")
    return "\n".join(lines)
