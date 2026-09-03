"""决策证据链核心逻辑（纯标准库）。

目标：让每条决策断言可追溯到证据；支持反证标记、覆盖检查、
Markdown/Mermaid 两种可读/可视化输出。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Evidence:
    evidence_id: str
    source_file: str
    quote: str = ""
    role: str = "support"  # support | counter | context


@dataclass
class Assertion:
    text: str
    evidence_ids: List[str] = field(default_factory=list)
    conclusion: bool = False


@dataclass
class EvidenceChain:
    question: str
    assertions: List[Assertion] = field(default_factory=list)
    evidence: Dict[str, Evidence] = field(default_factory=dict)

    def add_evidence(self, item: Evidence) -> None:
        self.evidence[item.evidence_id] = item

    def add_assertion(self, assertion: Assertion) -> None:
        self.assertions.append(assertion)


def check_assertion_coverage(chain: EvidenceChain) -> List[str]:
    """检查每条断言是否都有证据引用、证据 ID 是否存在、结论是否可达。"""
    issues: List[str] = []
    for idx, assertion in enumerate(chain.assertions, 1):
        if not assertion.text:
            issues.append(f"断言 {idx}: 内容为空")
        if not assertion.evidence_ids:
            issues.append(f"断言 {idx}: 缺少证据引用")
        for eid in assertion.evidence_ids:
            if eid not in chain.evidence:
                issues.append(f"断言 {idx}: 证据 {eid} 不存在")
    conclusions = [a for a in chain.assertions if a.conclusion]
    if not conclusions:
        issues.append("证据链缺少结论断言（conclusion=True）")
    return issues


def build_evidence_chain(question: str, assertions: List[dict],
                         evidence: List[dict]) -> EvidenceChain:
    """从结构化 JSON 构建 EvidenceChain。"""
    chain = EvidenceChain(question=question)
    for item in evidence:
        chain.add_evidence(Evidence(
            evidence_id=str(item["evidence_id"]),
            source_file=str(item.get("source_file", "")),
            quote=str(item.get("quote", "")),
            role=str(item.get("role", "support")),
        ))
    for item in assertions:
        chain.add_assertion(Assertion(
            text=str(item["text"]),
            evidence_ids=[str(x) for x in item.get("evidence_ids", [])],
            conclusion=bool(item.get("conclusion", False)),
        ))
    return chain


def render_markdown(chain: EvidenceChain) -> str:
    lines = [f"## 决策证据链", "", f"**问题**：{chain.question}", ""]
    lines.append("| 断言 | 结论 | 证据 |")
    lines.append("|---|---|---|")
    for assertion in chain.assertions:
        refs = ", ".join(assertion.evidence_ids) or "-"
        marker = "是" if assertion.conclusion else "否"
        lines.append(f"| {assertion.text} | {marker} | {refs} |")
    lines.extend(["", "### 证据清单", ""])
    for eid, item in chain.evidence.items():
        role = "反证" if item.role == "counter" else "支持/上下文"
        lines.append(f"- `{eid}`（{role}）：{item.source_file}"
                     + (f"：{item.quote}" if item.quote else ""))
    return "\n".join(lines)


def render_mermaid(chain: EvidenceChain) -> str:
    lines = ["flowchart LR"]
    for eid, item in chain.evidence.items():
        label = item.source_file.replace("|", "/")
        lines.append(f"    {eid}[\"{eid}: {label}\"]")
    for idx, assertion in enumerate(chain.assertions, 1):
        node = f"A{idx}"
        shape = "{{" if assertion.conclusion else "["
        end = "}}" if assertion.conclusion else "]"
        text = assertion.text[:36].replace('"', "'")
        lines.append(f"    {node}{shape}\"{text}\"{end}")
        for eid in assertion.evidence_ids:
            lines.append(f"    {eid} --> {node}")
    return "\n".join(lines)


def summarize_trace(chain: EvidenceChain) -> dict:
    issues = check_assertion_coverage(chain)
    return {
        "question": chain.question,
        "assertion_count": len(chain.assertions),
        "evidence_count": len(chain.evidence),
        "issues": issues,
        "traceable": not issues,
    }

