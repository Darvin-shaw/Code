"""MCP 服务核心逻辑测试（不依赖 mcp 包与文件写盘）。"""

from __future__ import annotations

import unittest

from mcp_servers.asset_cognition_server.asset_cognition_core import (
    find_assets_by_entity,
    new_asset_card,
    validate_asset_card,
)
from mcp_servers.decision_trace_server.decision_trace_core import (
    build_evidence_chain,
    check_assertion_coverage,
    render_markdown,
    render_mermaid,
    summarize_trace,
)
from mcp_servers.kg_ontology_server.kg_ontology_core import (
    GraphStore,
    diff_triples,
)


class AssetCognitionCoreTest(unittest.TestCase):
    def test_valid_card_passes(self) -> None:
        card = new_asset_card(
            source_file="03_quality_records/spc_hardness_axis_202505.csv",
            modality="table",
            doc_type="quality_record",
            business_tags=["2025-05", "AX-A", "HT-03"],
            entities=["AX-20250518-01", "HARD-HRC"],
            checksum="a" * 64,
        )
        self.assertEqual([], validate_asset_card(card))

    def test_invalid_card_reports_issues(self) -> None:
        card = {"asset_id": "bad-id", "modality": "unknown"}
        issues = validate_asset_card(card)
        self.assertTrue(any("必填" in issue for issue in issues))
        self.assertTrue(any("modality" in issue for issue in issues))

    def test_find_assets_by_entity(self) -> None:
        assets = [
            {"asset_id": "AST-20260903-0001", "source_file": "spc.csv",
             "business_tags": "AX-A;HT-03", "entities": "AX-20250518-01",
             "doc_type": "quality_record"},
            {"asset_id": "AST-20260903-0002", "source_file": "complaint.csv",
             "business_tags": "GB-G1", "entities": "CP-20250610-01",
             "doc_type": "quality_record"},
        ]
        hits = find_assets_by_entity(assets, "AX-20250518-01")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["asset_id"], "AST-20260903-0001")


class GraphOntologyCoreTest(unittest.TestCase):
    def test_in_memory_store(self) -> None:
        store = GraphStore(":memory:")
        try:
            store.add_entity("AX-20250518-01", "Batch", "电机轴 5/18 批次")
            store.add_entity("HT-03", "Equipment", "3 号热处理炉")
            store.add_triple({
                "subject_id": "AX-20250518-01",
                "predicate": "processed_in",
                "object_id": "HT-03",
                "confidence": 0.9,
                "status": "confirmed",
                "source": "seed",
            })
            result = store.search("AX-20250518-01", max_hops=1)
            self.assertEqual(result["entity_count"], 1)
            self.assertEqual(len(result["matches"][0]["edges"]), 1)
            self.assertEqual(store.get_triples("confirmed")[0]["object_id"], "HT-03")
        finally:
            store.close()

    def test_duplicate_triple_updates_not_duplicates(self) -> None:
        store = GraphStore(":memory:")
        try:
            for _ in range(2):
                store.add_triple({
                    "subject_id": "A", "predicate": "rel", "object_id": "B",
                    "status": "confirmed",
                })
            self.assertEqual(len(store.get_triples()), 1)
        finally:
            store.close()

    def test_diff_triples(self) -> None:
        before = [{"subject_id": "A", "predicate": "r", "object_id": "B"}]
        after = [
            {"subject_id": "A", "predicate": "r", "object_id": "B"},
            {"subject_id": "A", "predicate": "r2", "object_id": "C"},
        ]
        diff = diff_triples(before, after)
        self.assertEqual(len(diff["added"]), 1)
        self.assertEqual(len(diff["removed"]), 0)
        self.assertEqual(diff["unchanged_count"], 1)


class DecisionTraceCoreTest(unittest.TestCase):
    def _chain(self):
        return build_evidence_chain(
            question="该批能否让步接收？",
            assertions=[
                {"text": "实测低于规格下限", "evidence_ids": ["E1"],
                 "conclusion": False},
                {"text": "让步需客户书面同意", "evidence_ids": ["E2"],
                 "conclusion": True},
            ],
            evidence=[
                {"evidence_id": "E1", "source_file": "spc.csv",
                 "quote": "45.5-47.4 HRC", "role": "support"},
                {"evidence_id": "E2", "source_file": "QP-INC-03.md",
                 "quote": "4.3 让步接收", "role": "support"},
            ],
        )

    def test_coverage_and_summary(self) -> None:
        chain = self._chain()
        self.assertEqual([], check_assertion_coverage(chain))
        summary = summarize_trace(chain)
        self.assertTrue(summary["traceable"])
        self.assertEqual(summary["evidence_count"], 2)

    def test_missing_evidence_reported(self) -> None:
        chain = build_evidence_chain(
            question="q",
            assertions=[{"text": "无证据结论", "evidence_ids": [], "conclusion": True}],
            evidence=[],
        )
        issues = check_assertion_coverage(chain)
        self.assertTrue(any("缺少证据" in issue for issue in issues))

    def test_render(self) -> None:
        chain = self._chain()
        markdown = render_markdown(chain)
        mermaid = render_mermaid(chain)
        self.assertIn("决策证据链", markdown)
        self.assertIn("flowchart LR", mermaid)


if __name__ == "__main__":
    unittest.main()
