"""决策证据链 MCP 服务（FastMCP 包装）。"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_servers.decision_trace_server.decision_trace_core import (
    build_evidence_chain,
    check_assertion_coverage,
    render_markdown,
    render_mermaid,
    summarize_trace,
)


mcp = FastMCP("decision_trace_server")


@mcp.tool
def build_trace(question: str, assertions: list, evidence: list) -> dict:
    """构建决策证据链并返回 JSON 摘要。"""
    chain = build_evidence_chain(question, assertions, evidence)
    return summarize_trace(chain)


@mcp.tool
def check_trace(question: str, assertions: list, evidence: list) -> dict:
    """检查断言是否全部有证据覆盖。"""
    chain = build_evidence_chain(question, assertions, evidence)
    issues = check_assertion_coverage(chain)
    return {"traceable": not issues, "issues": issues}


@mcp.tool
def render_trace(question: str, assertions: list, evidence: list,
                 format: str = "markdown") -> dict:
    """渲染证据链为 Markdown 或 Mermaid。"""
    chain = build_evidence_chain(question, assertions, evidence)
    if format == "mermaid":
        return {"format": "mermaid", "content": render_mermaid(chain)}
    return {"format": "markdown", "content": render_markdown(chain)}


if __name__ == "__main__":
    mcp.run()
