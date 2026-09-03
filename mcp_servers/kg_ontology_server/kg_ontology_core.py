"""本体/知识图谱核心逻辑（纯标准库，SQLite 存储）。

为低资源场景提供：三元组写入、实体邻域检索、Schema 一致性检查、版本 diff。
设计上可作为 Neo4j 的轻量降级实现，也可作为评审/联调阶段的离线底座。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


TRIPLE_KEYS = ("subject_id", "predicate", "object_id")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_triples_jsonl(path: Path) -> List[dict]:
    triples: List[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"三元组解析失败 {path}:{line_no}") from exc
            for key in TRIPLE_KEYS:
                if not obj.get(key):
                    raise ValueError(f"三元组缺少字段 {key}: {path}:{line_no}")
            triples.append(obj)
    return triples


def write_triples_jsonl(path: Path, triples: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for triple in triples:
            fh.write(json.dumps(triple, ensure_ascii=False) + "\n")


def diff_triples(before: List[dict], after: List[dict]) -> Dict[str, List[dict]]:
    """按 (subject, predicate, object) 计算三元组版本差异。"""

    def key_of(triple: dict) -> Tuple[str, str, str]:
        return (triple["subject_id"], triple["predicate"], triple["object_id"])

    before_keys = {key_of(t) for t in before}
    after_keys = {key_of(t) for t in after}
    by_key = {key_of(t): t for t in after}
    added = [by_key[k] for k in sorted(after_keys - before_keys)]
    removed = [t for t in before if key_of(t) in before_keys - after_keys]
    return {
        "added": added,
        "removed": removed,
        "unchanged_count": len(before_keys & after_keys),
    }


class GraphStore:
    """轻量 SQLite 图存储（实体 + 三元组）。"""

    def __init__(self, db_path: Path | str = ":memory:"):
        if db_path != ":memory:":
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entities (
                entity_id   TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                name        TEXT NOT NULL,
                props       TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS triples (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id  TEXT NOT NULL,
                predicate   TEXT NOT NULL,
                object_id   TEXT NOT NULL,
                confidence  REAL NOT NULL DEFAULT 0.5,
                status      TEXT NOT NULL DEFAULT 'candidate',
                source      TEXT NOT NULL DEFAULT '',
                standard_ref TEXT NOT NULL DEFAULT '',
                version     TEXT NOT NULL DEFAULT 'v1',
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject_id);
            CREATE INDEX IF NOT EXISTS idx_triples_object ON triples(object_id);
            """
        )
        self.conn.commit()

    def add_entity(self, entity_id: str, entity_type: str, name: str,
                   props: Optional[dict] = None) -> None:
        self.conn.execute(
            """
            INSERT INTO entities(entity_id, entity_type, name, props)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                entity_type=excluded.entity_type,
                name=excluded.name,
                props=excluded.props
            """,
            (entity_id, entity_type, name, json.dumps(props or {}, ensure_ascii=False)),
        )
        self.conn.commit()

    def add_triple(self, triple: dict) -> None:
        if not all(triple.get(k) for k in TRIPLE_KEYS):
            raise ValueError("subject_id/predicate/object_id 不能为空")
        existing = self.conn.execute(
            """
            SELECT id FROM triples
            WHERE subject_id=? AND predicate=? AND object_id=?
            """,
            (triple["subject_id"], triple["predicate"], triple["object_id"]),
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE triples SET confidence=?, status=?, source=?,
                    standard_ref=?, version=?
                WHERE id=?
                """,
                (float(triple.get("confidence", 0.5)),
                 triple.get("status", "confirmed"),
                 triple.get("source", ""),
                 triple.get("standard_ref", ""),
                 triple.get("version", "v1"),
                 existing["id"]),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO triples(subject_id, predicate, object_id, confidence,
                                    status, source, standard_ref, version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (triple["subject_id"], triple["predicate"], triple["object_id"],
                 float(triple.get("confidence", 0.5)),
                 triple.get("status", "candidate"),
                 triple.get("source", ""),
                 triple.get("standard_ref", ""),
                 triple.get("version", "v1"),
                 triple.get("created_at", utc_now())),
            )
        self.conn.commit()

    def bulk_seed(self, triples: Iterable[dict]) -> int:
        count = 0
        for triple in triples:
            self.add_triple(triple)
            count += 1
        return count

    def entity(self, entity_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT entity_id, entity_type, name, props FROM entities WHERE entity_id=?",
            (entity_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_triples(self, status: str = "") -> List[dict]:
        sql = "SELECT * FROM triples"
        params: tuple = ()
        if status:
            sql += " WHERE status=?"
            params = (status,)
        sql += " ORDER BY id"
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def search(self, keyword: str, max_hops: int = 1) -> dict:
        """按实体名/ID 关键词返回实体及其邻域。"""
        entity_rows = self.conn.execute(
            "SELECT * FROM entities WHERE entity_id LIKE ? OR name LIKE ?",
            (f"%{keyword}%", f"%{keyword}%"),
        ).fetchall()
        results: List[dict] = []
        seen_entities: set = set()
        for row in entity_rows:
            current = {row["entity_id"]}
            hop_entities = {row["entity_id"]}
            edges: List[dict] = []
            for _ in range(max(1, max_hops)):
                placeholders = ",".join("?" for _ in hop_entities)
                if not hop_entities:
                    break
                edge_rows = self.conn.execute(
                    f"""
                    SELECT * FROM triples
                    WHERE subject_id IN ({placeholders}) OR object_id IN ({placeholders})
                    """,
                    tuple(hop_entities) + tuple(hop_entities),
                ).fetchall()
                next_hop: set = set()
                for edge in edge_rows:
                    edges.append(dict(edge))
                    next_hop.add(edge["subject_id"])
                    next_hop.add(edge["object_id"])
                hop_entities = next_hop - seen_entities
                seen_entities |= next_hop
            results.append({
                "entity": dict(row),
                "edges": edges,
            })
        return {"matches": results, "entity_count": len(results)}
