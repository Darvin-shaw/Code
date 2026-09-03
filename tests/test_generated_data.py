"""生成产物一致性测试（data/generated 存在时运行，否则跳过）。"""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "data" / "generated"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


@unittest.skipUnless(GENERATED.joinpath("manifest.json").exists(),
                     "data/generated 尚未生成，跳过一致性测试")
class GeneratedDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (GENERATED / "manifest.json").open(encoding="utf-8") as fh:
            cls.manifest = json.load(fh)

    def test_manifest_counts(self) -> None:
        self.assertEqual(self.manifest["file_count"], self.manifest["asset_ledger_count"])
        self.assertGreaterEqual(self.manifest["asset_ledger_count"], 15)

    def test_ledger_rows_exist_and_hash_match(self) -> None:
        ledger_path = GENERATED / "assets_ledger.csv"
        with ledger_path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreaterEqual(len(rows), 15)
        ids = [row["asset_id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)), "asset_id 应唯一")
        for row in rows:
            source = GENERATED / row["source_file"]
            self.assertTrue(source.exists(), f"台账指向不存在的文件: {source}")
            self.assertEqual(row["checksum"], sha256_of(source))

    def test_golden_evidence_exists(self) -> None:
        from pathlib import Path as _P

        golden_path = _P(__file__).resolve().parents[1] / "tests" / "golden" / "golden_qa_v1.json"
        with golden_path.open(encoding="utf-8") as fh:
            golden = json.load(fh)
        for item in golden:
            for rel in item["required_evidence"]:
                self.assertTrue((GENERATED / rel).exists(),
                                f"{item['id']} 缺少证据文件: {rel}")

    def test_core_assets_present(self) -> None:
        expected = {
            "03_quality_records/spc_hardness_axis_202505.csv",
            "03_quality_records/maintenance_logs.csv",
            "03_quality_records/nonconformity_records.csv",
            "03_quality_records/inspection_records_2025H1.csv",
            "02_quality_docs/QP-INC-03-不合格品控制程序.md",
            "02_quality_docs/SP-INSP-AX-电机轴检验规范.md",
        }
        present = {row["source_file"] for row in self.ledger_rows()}
        self.assertTrue(expected.issubset(present))

    @classmethod
    def ledger_rows(cls) -> list[dict]:
        with (GENERATED / "assets_ledger.csv").open(encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))


if __name__ == "__main__":
    unittest.main()

