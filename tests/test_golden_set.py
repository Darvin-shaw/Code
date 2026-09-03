"""Golden 评测集格式校验。"""

from __future__ import annotations

import unittest

from run_eval import load_golden, validate_golden


ROOT = None  # run_eval 自身基于文件定位，无需此处重复


class GoldenSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "tests" / "golden" / "golden_qa_v1.json"
        cls.data = load_golden(path)

    def test_nonempty(self) -> None:
        self.assertGreaterEqual(len(self.data), 10)

    def test_all_valid(self) -> None:
        errors = validate_golden(self.data)
        self.assertEqual([], errors)

    def test_coverage_of_types(self) -> None:
        types = {item["type"] for item in self.data}
        self.assertIn("root-cause", types)
        self.assertIn("disposition", types)
        self.assertIn("multimodal", types)


if __name__ == "__main__":
    unittest.main()
