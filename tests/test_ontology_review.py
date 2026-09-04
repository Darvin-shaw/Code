"""T3.3 候选三元组人工/自动审核闭环测试。"""

from __future__ import annotations

import unittest


def sample_candidates() -> list[dict]:
    return [
        {
            "subject_id": "QP-INC-03", "subject_type": "QualityDocument",
            "predicate": "references", "object_id": "SP-INSP-AX",
            "object_type": "QualityDocument", "confidence": 0.8,
            "status": "candidate", "source": "rule-doc", "standard_ref": "",
            "version": "v1", "file_ref": "02_quality_docs/QP-INC-03-不合格品控制程序.md",
        },
        {
            "subject_id": "SP-INSP-AX", "subject_type": "QualityDocument",
            "predicate": "references", "object_id": "WI-HT-AX",
            "object_type": "QualityDocument", "confidence": 0.3,
            "status": "candidate", "source": "llm-candidate", "standard_ref": "",
            "version": "v1", "file_ref": "02_quality_docs/SP-INSP-AX-电机轴检验规范.md",
        },
        {
            "subject_id": "HT-03", "subject_type": "Equipment",
            "predicate": "has_maintenance", "object_id": "MT-20250520-01",
            "object_type": "MaintenanceRecord", "confidence": 0.95,
            "status": "candidate", "source": "rule-record", "standard_ref": "",
            "version": "v1", "file_ref": "03_quality_records/maintenance_logs.csv",
        },
    ]


class OntologyReviewTest(unittest.TestCase):
    def test_triple_key_is_stable(self) -> None:
        from ontology.review_core import triple_key

        key = triple_key(sample_candidates()[0])
        self.assertEqual(("QP-INC-03", "references", "SP-INSP-AX"), key)

    def test_auto_confirm_high_confidence(self) -> None:
        from ontology.review_core import split_auto_vs_human

        auto, human = split_auto_vs_human(sample_candidates(), auto_threshold=0.9)
        self.assertEqual(len(auto), 1)
        self.assertEqual(auto[0]["predicate"], "has_maintenance")
        self.assertEqual(len(human), 2)

    def test_apply_review_marks_status_and_reason(self) -> None:
        from ontology.review_core import apply_review

        candidate = sample_candidates()[1]
        result = apply_review(candidate, "confirmed", reason="规则与维保台账一致",
                              reviewer="qa-reviewer")
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["reviewed_by"], "qa-reviewer")
        self.assertIn("reviewed_at", result)

    def test_reject_is_kept_out_of_confirmed(self) -> None:
        from ontology.review_core import apply_review

        result = apply_review(sample_candidates()[0], "rejected",
                              reason="引用链不成立", reviewer="tester")
        self.assertEqual(result["status"], "rejected")
        self.assertTrue(result["decision_reason"])

    def test_invalid_decision_rejected(self) -> None:
        from ontology.review_core import apply_review

        with self.assertRaises(ValueError):
            apply_review(sample_candidates()[0], "maybe", reviewer="tester")

    def test_review_sheet_can_render_table(self) -> None:
        from ontology.review_core import render_review_sheet

        sheet = render_review_sheet(sample_candidates())
        self.assertIn("subject_id", sheet)
        self.assertIn("QP-INC-03", sheet)

    def test_apply_policy_splits_confirmed_rejected_pending(self) -> None:
        from ontology.review_core import apply_policy

        candidates = [
            {**sample_candidates()[0], "confidence": 0.95},
            {**sample_candidates()[1], "confidence": 0.2},
            {**sample_candidates()[2], "confidence": 0.55},
        ]
        confirmed, rejected, pending = apply_policy(
            candidates, confirm_threshold=0.9, reject_threshold=0.4)
        self.assertEqual(len(confirmed), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(len(pending), 1)


if __name__ == "__main__":
    unittest.main()
