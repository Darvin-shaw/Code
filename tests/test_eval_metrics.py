"""M5 T5.1 离线评测指标测试。"""

from __future__ import annotations

import unittest


class EvalMetricsTest(unittest.TestCase):
    def test_evidence_recall(self) -> None:
        from tests.eval_metrics import evidence_recall

        self.assertEqual(evidence_recall({"a", "b"}, {"a", "c"}), 0.5)

    def test_evidence_precision(self) -> None:
        from tests.eval_metrics import evidence_precision

        self.assertEqual(evidence_precision({"a", "b"}, {"a", "c"}), 0.5)

    def test_forbidden_evidence_violation(self) -> None:
        from tests.eval_metrics import forbidden_violations

        bad = forbidden_violations({"a", "x"}, {"x", "y"})
        self.assertEqual(bad, ["x"])

    def test_traceability_complete(self) -> None:
        from tests.eval_metrics import traceability_complete

        self.assertTrue(traceability_complete({"e1", "e2"}, ["a", "b"]))
        self.assertFalse(traceability_complete({"e1"}, ["a", "b"]))

    def test_aggregate_case_metrics(self) -> None:
        from tests.eval_metrics import score_case

        score = score_case(
            required={"spc.csv", "qp.md"},
            forbidden={"complaint.csv"},
            retrieved={"spc.csv", "qp.md", "complaint.csv"},
            assertions_evidence={1: ["e1"], 2: ["e2"]},
        )
        self.assertEqual(score["recall"], 1.0)
        self.assertEqual(score["precision"], 2 / 3)
        self.assertEqual(score["forbidden_violations"], ["complaint.csv"])
        self.assertTrue(score["traceable"])


if __name__ == "__main__":
    unittest.main()
