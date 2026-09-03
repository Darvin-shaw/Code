"""图谱本体 MCP 服务（FastMCP 包装）。"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from mcp_servers.common import project_root
from mcp_servers.kg_ontology_server.kg_ontology_core import (
    GraphStore,
    diff_triples,
    load_triples_jsonl,
)


DEFAULT_DB = project_root() / "data" / "graph_store.sqlite"

mcp = FastMCP("kg_ontology_server")


def _store(db_path: str = "") -> GraphStore:
    return GraphStore(Path(db_path) if db_path else DEFAULT_DB)


@mcp.tool
def graph_search(keyword: str, max_hops: int = 1, db_path: str = "") -> dict:
    """按实体关键词检索本体图并返回邻域（实体+边）。"""
    store = _store(db_path)
    try:
        return store.search(keyword, max_hops=max_hops)
    finally:
        store.close()


@mcp.tool
def add_triple(
    subject_id: str,
    predicate: str,
    object_id: str,
    confidence: float = 0.8,
    status: str = "confirmed",
    source: str = "",
    standard_ref: str = "",
    db_path: str = "",
) -> dict:
    """写入（或更新）一条三元组。"""
    store = _store(db_path)
    try:
        store.add_triple({
            "subject_id": subject_id,
            "predicate": predicate,
            "object_id": object_id,
            "confidence": confidence,
            "status": status,
            "source": source,
            "standard_ref": standard_ref,
        })
        return {"ok": True, "triple": {
            "subject_id": subject_id, "predicate": predicate, "object_id": object_id,
        }}
    finally:
        store.close()


@mcp.tool
def ontology_diff(before_path: str, after_path: str) -> dict:
    """比较两个三元组 JSONL 快照，输出新增/删除/未变。"""
    before = load_triples_jsonl(Path(before_path))
    after = load_triples_jsonl(Path(after_path))
    return diff_triples(before, after)


if __name__ == "__main__":
    mcp.run()

