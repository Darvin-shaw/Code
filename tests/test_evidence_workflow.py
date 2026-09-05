"""M4 T4.2 证据链决策工作流测试。"""

from __future__ import annotations

import unittest


class EvidenceWorkflowTest(unittest.TestCase):
    def test_run_workflow_returns_traceable_answer(self) -> None:
        from mcp_servers.decision_trace_server.evidence_workflow import run_evidence_workflow

        result = run_evidence_workflow(
            question="该批 42 件硬度不合格能否让步接收？",
            assertions=[
                {"text": "实测低于规格下限", "evidence_ids": ["E1"],
                 "conclusion": False},
                {"text": "让步需客户书面同意", "evidence_ids": ["E2"],
                 "conclusion": True},
            ],
            evidence=[
                {"evidence_id": "E1", "source_file": "spc.csv",
                 "quote": "45.5-47.4", "role": "support"},
                {"evidence_id": "E2", "source_file": "QP-INC-03.md",
                 "quote": "4.3", "role": "support"},
            ],
        )
        self.assertEqual(result["route"]["category"], "disposition")
        self.assertTrue(result["traceable"])
        self.assertIn("证据链", result["markdown"])
        self.assertIn("flowchart", result["mermaid"])

    def test_missing_evidence_marks_untraceable(self) -> None:
        from mcp_servers.decision_trace_server.evidence_workflow import run_evidence_workflow

        result = run_evidence_workflow(
            question="为什么硬度偏低？",
            assertions=[{"text": "无证据结论", "evidence_ids": [], "conclusion": True}],
            evidence=[],
        )
        self.assertFalse(result["traceable"])
        self.assertTrue(result["issues"])


if __name__ == "__main__":
    unittest.main()
