"""M5 T5.2 版本回归门与演化报告测试。"""

from __future__ import annotations

import unittest


class EvolutionGateTest(unittest.TestCase):
    def test_gate_passes_when_metric_improves(self) -> None:
        from ontology.evolution_gate import regression_gate

        self.assertTrue(regression_gate(
            {"recall": 0.80, "precision": 0.70},
            {"recall": 0.85, "precision": 0.72},
            tolerance=0.05))

    def test_gate_fails_when_recall_drops(self) -> None:
        from ontology.evolution_gate import regression_gate

        self.assertFalse(regression_gate(
            {"recall": 0.90, "precision": 0.70},
            {"recall": 0.82, "precision": 0.71},
            tolerance=0.05))

    def test_evolution_report_includes_version_and_gate(self) -> None:
        from ontology.evolution_gate import evolution_report

        report = evolution_report(
            old_version="v1", new_version="v2",
            old_scores={"recall": 0.90},
            new_scores={"recall": 0.95},
            changes=["新增 2026 条款对齐"],
            tolerance=0.05,
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["old_version"], "v1")
        self.assertEqual(report["new_version"], "v2")
        self.assertIn("新增 2026 条款对齐", report["changes"])


if __name__ == "__main__":
    unittest.main()
