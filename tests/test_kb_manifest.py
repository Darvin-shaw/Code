"""T2.2 知识库 manifest 与表格摘要工具测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.load_knowledge_bases import build_manifest, classify_files


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated"


@unittest.skipUnless((ROOT / "data" / "generated" / "manifest.json").exists(),
                     "data/generated 尚未生成，跳过 T2.2 测试")
class KnowledgeBaseManifestTest(unittest.TestCase):
    def test_classify_three_groups(self) -> None:
        groups = classify_files(DATA)
        self.assertIn("kb_standard", groups)
        self.assertIn("kb_records", groups)
        self.assertIn("kb_visual", groups)
        self.assertGreaterEqual(len(groups["kb_standard"]), 5)
        self.assertGreaterEqual(len(groups["kb_records"]), 11)

    def test_manifest_files_exist(self) -> None:
        manifest = build_manifest(DATA)
        total = 0
        for kb in manifest["knowledge_bases"]:
            total += kb["file_count"]
            for item in kb["files"]:
                self.assertTrue((DATA / item["file"]).exists(),
                                f"manifest 指向缺失文件: {item['file']}")
        self.assertEqual(total, manifest["total_files"])

    def test_table_summary_generation(self) -> None:
        target = DATA / "03_quality_records" / "table_summaries"
        if target.exists() and any(target.glob("*.md")):
            return
        self.skipTest("table_summaries 未生成，调用 --build-summaries 后复测")


if __name__ == "__main__":
    unittest.main()
