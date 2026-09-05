"""M4 T4.2 证据链决策工作流（纯逻辑）。

把“检索路由 + 证据链构建 + 覆盖检查 + Markdown/Mermaid 渲染”编排为
一个可离线调用的执行流，供后续 Skill/Agent 复用。
"""

from __future__ import annotations

from typing import Dict, List

from mcp_servers.decision_trace_server.decision_trace_core import (
    build_evidence_chain,
    check_assertion_coverage,
    render_markdown,
    render_mermaid,
    summarize_trace,
)
from mcp_servers.decision_trace_server.retrieval_router import route_question


def run_evidence_workflow(question: str,
                          assertions: List[dict],
                          evidence: List[dict]) -> Dict[str, object]:
    """执行证据链决策流程并返回路由、痕迹与可读/可视化输出。"""
    route = route_question(question)
    chain = build_evidence_chain(question, assertions, evidence)
    issues = check_assertion_coverage(chain)
    return {
        "route": route,
        "question": question,
        "summary": summarize_trace(chain),
        "traceable": not issues,
        "issues": issues,
        "markdown": render_markdown(chain),
        "mermaid": render_mermaid(chain),
    }
