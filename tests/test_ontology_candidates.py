"""T3.2 候选抽取管线测试。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from mcp_servers.kg_ontology_server.kg_ontology_core import GraphStore


ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str):
    with (ROOT / rel).open(encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(rel: str) -> list[dict]:
    rows: list[dict] = []
    path = ROOT / rel
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


@unittest.skipUnless((ROOT / "data" / "generated" / "manifest.json").exists(),
                     "合成数据未生成，跳过 T3.2 抽取测试")
class OntologyCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import sys

        sys.path.insert(0, str(ROOT))
        from scripts.ontology_candidates import run_extraction

        cls.extraction = run_extraction()
        cls.schema = load_json("ontology/schema-v1.json")
        cls.seed = load_jsonl("ontology/seed-triples.jsonl")

    def test_nonempty(self) -> None:
        self.assertGreaterEqual(len(self.extraction), 5)

    def test_schema_valid_and_not_duplicating_seed(self) -> None:
        seed_keys = {(t["subject_id"], t["predicate"], t["object_id"]) for t in self.seed}
        relations = self.schema["relations"]
        statuses = self.schema["triple_properties"]["status"]["enum"]
        for triple in self.extraction:
            key = (triple["subject_id"], triple["predicate"], triple["object_id"])
            self.assertNotIn(key, seed_keys, "候选不应重复种子事实")
            self.assertIn(triple["predicate"], relations)
            rel = relations[triple["predicate"]]
            self.assertIn(triple["subject_type"], rel["subject_types"])
            self.assertIn(triple["object_type"], rel["object_types"])
            self.assertIn(triple["status"], statuses)

    def test_status_coverage(self) -> None:
        statuses = {t["status"] for t in self.extraction}
        self.assertIn("candidate", statuses)
        self.assertIn("confirmed", statuses)

    def test_loadable_into_graph(self) -> None:
        store = GraphStore(":memory:")
        try:
            store.bulk_seed(self.extraction)
            self.assertEqual(len(store.get_triples()), len(self.extraction))
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
