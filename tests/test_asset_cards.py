"""资产卡片 Schema 与样例校验。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str):
    with (ROOT / rel).open(encoding="utf-8") as fh:
        return json.load(fh)


class AssetCardSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json("data/asset_card_schema.json")
        cls.example = load_json("data/static/asset_card.example.json")

    def test_schema_required_fields(self) -> None:
        required = {
            "asset_id", "source_file", "modality", "doc_type",
            "business_tags", "entities", "checksum", "ingested_at",
        }
        self.assertTrue(required.issubset(set(self.schema["required"])))

    def test_example_has_required_fields(self) -> None:
        for field_name in self.schema["required"]:
            self.assertIn(field_name, self.example)

    def test_asset_id_pattern(self) -> None:
        self.assertRegex(self.example["asset_id"], r"^AST-\d{8}-\d{4}$")

    def test_modality_enum(self) -> None:
        self.assertIn(self.example["modality"], self.schema["properties"]["modality"]["enum"])

    def test_checksum_pattern(self) -> None:
        self.assertRegex(self.example["checksum"], r"^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main()

