"""T3.1 本体 Schema / 标准映射 / 种子三元组一致性测试。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from mcp_servers.kg_ontology_server.kg_ontology_core import GraphStore


ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str):
    with (ROOT / rel).open(encoding="utf-8") as fh:
        return json.load(fh)


def load_seed_triples() -> list[dict]:
    triples: list[dict] = []
    with (ROOT / "ontology" / "seed-triples.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                triples.append(json.loads(line))
    return triples


class OntologySchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json("ontology/schema-v1.json")
        cls.standards = load_json("ontology/standards-map.json")
        cls.triples = load_seed_triples()

    def test_schema_basics(self) -> None:
        self.assertGreaterEqual(len(self.schema["classes"]), 10)
        self.assertGreaterEqual(len(self.schema["relations"]), 12)

    def test_relation_types_exist(self) -> None:
        for rel_name, rel in self.schema["relations"].items():
            for entity_type in rel["subject_types"] + rel["object_types"]:
                self.assertIn(entity_type, self.schema["classes"],
                              f"关系 {rel_name} 引用未知类 {entity_type}")

    def test_seed_triples_schema_valid(self) -> None:
        self.assertGreaterEqual(len(self.triples), 25)
        ids = [t["id"] for t in self.triples]
        self.assertEqual(len(ids), len(set(ids)), "种子三元组 id 重复")
        relations = self.schema["relations"]
        statuses = self.schema["triple_properties"]["status"]["enum"]
        for triple in self.triples:
            self.assertIn(triple["predicate"], relations,
                          f"{triple['id']} 使用未定义关系 {triple['predicate']}")
            rel = relations[triple["predicate"]]
            self.assertIn(triple["subject_type"], rel["subject_types"],
                          f"{triple['id']} subject 类型不合规")
            self.assertIn(triple["object_type"], rel["object_types"],
                          f"{triple['id']} object 类型不合规")
            self.assertIn(triple["status"], statuses)
            self.assertTrue(0.0 <= triple["confidence"] <= 1.0)

    def test_standard_refs_exist_in_map(self) -> None:
        clause_ids = {m["clause_id"] for m in self.standards["mappings"]}
        for triple in self.triples:
            ref = triple.get("standard_ref", "")
            if ref:
                self.assertIn(ref, clause_ids,
                              f"{triple['id']} 引用未登记标准锚点 {ref}")

    def test_seed_loadable_into_graph(self) -> None:
        store = GraphStore(":memory:")
        try:
            count = store.bulk_seed(self.triples)
            self.assertEqual(count, len(self.triples))
            self.assertEqual(len(store.get_triples()), len(self.triples))
        finally:
            store.close()

    def test_confirmed_triples_cover_core_chain(self) -> None:
        confirmed = {(t["subject_id"], t["predicate"], t["object_id"])
                     for t in self.triples if t["status"] == "confirmed"}
        self.assertIn(("AX-20250518-01", "produced_in", "HT-AX"), confirmed)
        self.assertIn(("HT-AX", "executed_on", "HT-03"), confirmed)
        self.assertIn(("IR-20250518-01", "detected", "DEF-HARD-LOW"), confirmed)
        self.assertIn(("DISP-REWORK", "based_on", "QP-INC-03"), confirmed)


if __name__ == "__main__":
    unittest.main()
