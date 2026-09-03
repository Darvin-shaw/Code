"""资产认知 MCP 服务（FastMCP 包装）。

安装依赖后运行：python -m mcp_servers.asset_cognition_server.server
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

from mcp_servers.asset_cognition_server.asset_cognition_core import (
    find_assets_by_entity,
    load_assets,
    register_asset,
    validate_asset_card,
)
from mcp_servers.common import project_root


DEFAULT_LEDGER = project_root() / "data" / "generated" / "assets_ledger.csv"

mcp = FastMCP("asset_cognition_server")


def _resolve_ledger(ledger_path: str | None) -> Path:
    return Path(ledger_path) if ledger_path else DEFAULT_LEDGER


@mcp.tool
def validate_asset_card(card: dict) -> dict:
    """校验资产卡片字段，返回 valid 与 issues。"""
    issues = validate_asset_card(card)
    return {"valid": not issues, "issues": issues}


@mcp.tool
def register_asset_tool(
    card: dict,
    ledger_path: str = "",
    source_root: str = "",
) -> dict:
    """登记一条资产卡片到台账 CSV；checksum 缺失时可按 source_root 自动计算。"""
    root = Path(source_root) if source_root else project_root() / "data" / "generated"
    row = register_asset(_resolve_ledger(ledger_path or None), card, source_root=root)
    return {"registered": True, "asset": row}


@mcp.tool
def find_assets_by_entity_tool(
    keyword: str,
    ledger_path: str = "",
    limit: int = 10,
) -> dict:
    """按实体/业务标签/文件名检索资产台账。"""
    assets = load_assets(_resolve_ledger(ledger_path or None))
    hits = find_assets_by_entity(assets, keyword, limit=limit)
    return {"count": len(hits), "assets": hits}


if __name__ == "__main__":
    mcp.run()

