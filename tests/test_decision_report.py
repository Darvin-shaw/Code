"""M4 T4.4 决策溯源报告生成测试。"""

from __future__ import annotations

import unittest


class DecisionReportTest(unittest.TestCase):
    def test_full_report_includes_sections(self) -> None:
        from mcp_servers.decision_trace_server.decision_report import render_full_report

        report = render_full_report(
            question="该批能否让步接收？",
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
        self.assertIn("决策报告", report)
        self.assertIn("结论与依据", report)
        self.assertIn("证据清单", report)
        self.assertIn("flowchart LR", report)
        self.assertIn("E1", report)

    def test_report_marks_untraceable(self) -> None:
        from mcp_servers.decision_trace_server.decision_report import render_full_report

        report = render_full_report(
            question="为什么硬度偏低？",
            assertions=[{"text": "无证据结论", "evidence_ids": [], "conclusion": True}],
            evidence=[],
        )
        self.assertIn("证据不足/未通过审计", report)


if __name__ == "__main__":
    unittest.main()
