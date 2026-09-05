"""M4 T4.1 检索路由与查询分解测试。"""

from __future__ import annotations

import unittest


class QueryRouterTest(unittest.TestCase):
    def test_route_disposition_question(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import route_question

        route = route_question("AX-20250518-01 批次能否让步接收？依据是什么？")
        self.assertEqual(route["category"], "disposition")
        self.assertIn("kb_standard", route["kb_priority"])
        self.assertTrue(route["needs_graph"])

    def test_route_numeric_question(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import route_question

        route = route_question("该批 42 件硬度实测范围是多少？")
        self.assertEqual(route["category"], "numeric")
        self.assertIn("kb_records", route["kb_priority"])

    def test_route_doc_lookup_question(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import route_question

        route = route_question("让步接收的条款依据出自哪个文件？")
        self.assertEqual(route["category"], "doc-lookup")

    def test_route_multimodal_question(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import route_question

        route = route_question("请解读这张 SPC 控制图并说明越限点")
        self.assertEqual(route["category"], "multimodal")
        self.assertIn("kb_visual", route["kb_priority"])

    def test_decompose_question_on_separator(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import decompose_question

        parts = decompose_question("批次硬度不合格；是否与 HT-03 温漂相关")
        self.assertEqual(len(parts), 2)

    def test_decompose_single_question_keeps_one(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import decompose_question

        parts = decompose_question("该批能否让步接收")
        self.assertEqual(len(parts), 1)

    def test_evidence_plan_has_steps(self) -> None:
        from mcp_servers.decision_trace_server.retrieval_router import evidence_plan

        plan = evidence_plan("该批 42 件硬度不合格是否与 3 号炉相关？")
        self.assertIn("route", plan)
        self.assertGreaterEqual(len(plan["steps"]), 3)
        self.assertEqual(plan["steps"][0]["action"], "retrieve")


if __name__ == "__main__":
    unittest.main()
