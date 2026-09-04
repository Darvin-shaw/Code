"""T3.4 标准对齐与增量/漂移检测测试。"""

from __future__ import annotations

import unittest


def sample_mappings_v1() -> list[dict]:
    return [
        {"clause_id": "STD:GB/T19001:8.7", "source_title": "不合格输出控制（摘要）",
         "internal_docs": ["QP-INC-03"], "ontology_terms": ["Defect", "DispositionDecision"]},
        {"clause_id": "STD:GB/T19001:8.6", "source_title": "放行（摘要）",
         "internal_docs": ["SP-INSP-AX"], "ontology_terms": ["InspectionRecord"]},
    ]


def sample_triples() -> list[dict]:
    return [
        {"subject_id": "QP-INC-03", "predicate": "aligns_with",
         "object_id": "STD:GB/T19001:8.7", "standard_ref": "STD:GB/T19001:8.7"},
        {"subject_id": "SP-INSP-AX", "predicate": "aligns_with",
         "object_id": "STD:GB/T19001:8.6", "standard_ref": "STD:GB/T19001:8.6"},
        {"subject_id": "WI-HT-AX", "predicate": "aligns_with",
         "object_id": "STD:GB/T19001:8.5", "standard_ref": "STD:GB/T19001:8.5"},
    ]


class StandardAlignmentTest(unittest.TestCase):
    def test_apply_delta_adds_new_clause(self) -> None:
        from ontology.standard_alignment import apply_delta

        delta = {
            "add": [
                {"clause_id": "STD:GB/T19001:2026:8.7.1",
                 "source_title": "不合格输出控制 2026 修订（摘要）",
                 "internal_docs": ["QP-INC-03"], "ontology_terms": ["DispositionDecision"]}
            ]
        }
        updated = apply_delta(sample_mappings_v1(), delta)
        self.assertEqual(len(updated), 3)
        self.assertTrue(any(m["clause_id"] == "STD:GB/T19001:2026:8.7.1" for m in updated))

    def test_compare_maps_reports_added_and_removed(self) -> None:
        from ontology.standard_alignment import compare_maps

        updated = sample_mappings_v1() + [{
            "clause_id": "STD:GB/T19001:2026:8.7.1",
            "source_title": "新条款（摘要）", "internal_docs": ["QP-INC-03"],
            "ontology_terms": ["DispositionDecision"],
        }]
        result = compare_maps(sample_mappings_v1(), updated)
        self.assertEqual(result["added"], ["STD:GB/T19001:2026:8.7.1"])
        self.assertEqual(result["removed"], [])

    def test_find_affected_triples_by_standard_ref(self) -> None:
        from ontology.standard_alignment import find_affected_triples

        affected = find_affected_triples(
            sample_triples(), {"STD:GB/T19001:2026:8.7.1", "STD:GB/T19001:8.7"})
        self.assertEqual(len(affected), 1)
        self.assertEqual(affected[0]["subject_id"], "QP-INC-03")

    def test_orphan_standard_ref_reported(self) -> None:
        from ontology.standard_alignment import orphan_refs

        known = {m["clause_id"] for m in sample_mappings_v1()}
        orphans = orphan_refs(sample_triples(), known)
        self.assertEqual(orphans, {"STD:GB/T19001:8.5"})

    def test_coverage_summary_counts_mappings(self) -> None:
        from ontology.standard_alignment import coverage_summary

        summary = coverage_summary(sample_mappings_v1())
        self.assertEqual(summary["total_mappings"], 2)
        self.assertEqual(summary["mapped_internal_docs"], {"QP-INC-03", "SP-INSP-AX"})

    def test_build_drift_report_combines_diff_and_impact(self) -> None:
        from ontology.standard_alignment import build_drift_report

        new_clause = {
            "clause_id": "STD:GB/T19001:2026:8.7.1",
            "source_title": "新条款（摘要）", "internal_docs": ["QP-INC-03"],
            "ontology_terms": ["DispositionDecision"],
        }
        report = build_drift_report(
            sample_mappings_v1(), sample_mappings_v1() + [new_clause], sample_triples())
        self.assertEqual(report["diff"]["added"], ["STD:GB/T19001:2026:8.7.1"])
        self.assertEqual(report["affected_triple_count"], 1)


if __name__ == "__main__":
    unittest.main()
