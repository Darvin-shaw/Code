"""资产认知核心逻辑（纯标准库，可独立单测）。

目标：把异构文件（PDF/表格/图片等）的解析结果统一成「资产卡片」，
支持注册、校验、按实体/标签检索，作为 Nexent 知识库之外的资产台账层。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from mcp_servers.common import (
    append_csv_row,
    load_rows,
    sha256_of,
)


ASSET_ID_PATTERN = re.compile(r"^AST-\d{8}-\d{4}$")
CHECKSUM_PATTERN = re.compile(r"^[a-f0-9]{64}$")
MODALITIES = {"text", "table", "image", "audio", "video", "mixed"}
REQUIRED_FIELDS = {
    "asset_id", "source_file", "modality", "doc_type",
    "business_tags", "entities", "checksum", "ingested_at",
}
LEDGER_FIELDS = [
    "asset_id", "source_file", "modality", "doc_type",
    "business_tags", "entities", "checksum", "chunk_ids", "ingested_at",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_asset_id(assets: List[dict] | None = None) -> str:
    """生成资产 ID：AST-YYYYMMDD-NNNN。"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    existing = [a.get("asset_id", "") for a in (assets or [])]
    seq = 1
    prefix = f"AST-{today}-"
    if existing:
        max_seq = max(
            (int(m.group(1)) for item in existing
             if (m := re.fullmatch(r"AST-\d{8}-(\d{4})", str(item)))),
            default=0,
        )
        seq = max_seq + 1
    return f"{prefix}{seq:04d}"


def new_asset_card(
    source_file: str,
    modality: str,
    doc_type: str,
    business_tags: List[str] | None = None,
    entities: List[str] | None = None,
    checksum: str = "",
    chunk_ids: List[str] | None = None,
    asset_id: str = "",
) -> dict:
    return {
        "asset_id": asset_id,
        "source_file": source_file,
        "modality": modality,
        "doc_type": doc_type,
        "business_tags": list(business_tags or []),
        "entities": list(entities or []),
        "checksum": checksum,
        "chunk_ids": list(chunk_ids or []),
        "ingested_at": utc_now(),
    }


def validate_asset_card(card: dict) -> List[str]:
    """返回问题列表；空列表表示合法。"""
    issues: List[str] = []
    missing = REQUIRED_FIELDS - set(card)
    if missing:
        issues.append(f"缺少必填字段: {sorted(missing)}")
    if "asset_id" in card and card["asset_id"] and not ASSET_ID_PATTERN.fullmatch(str(card["asset_id"])):
        issues.append(f"asset_id 格式不合法: {card['asset_id']}")
    if "modality" in card and card["modality"] not in MODALITIES:
        issues.append(f"modality 不合法: {card['modality']}")
    if "checksum" in card and card["checksum"] and not CHECKSUM_PATTERN.fullmatch(str(card["checksum"])):
        issues.append("checksum 必须是 64 位小写十六进制")
    return issues


def load_assets(ledger_path: Path) -> List[dict]:
    return load_rows(ledger_path)


def register_asset(
    ledger_path: Path,
    card: dict,
    source_root: Path | None = None,
) -> dict:
    """校验并登记资产卡片到台账 CSV。

    checksum 为空时，若 source_root 下存在 source_file 则自动计算 SHA-256。
    """
    issues = validate_asset_card(card)
    if issues:
        raise ValueError("; ".join(issues))

    assets = []
    if ledger_path.exists():
        assets = load_assets(ledger_path)
    if not card.get("asset_id"):
        card["asset_id"] = next_asset_id(assets)
    if not card.get("checksum") and source_root is not None:
        source = source_root / card["source_file"]
        if source.exists():
            card["checksum"] = sha256_of(source)

    row = {
        "asset_id": card.get("asset_id", ""),
        "source_file": card.get("source_file", ""),
        "modality": card.get("modality", ""),
        "doc_type": card.get("doc_type", ""),
        "business_tags": ";".join(card.get("business_tags") or []),
        "entities": ";".join(card.get("entities") or []),
        "checksum": card.get("checksum", ""),
        "chunk_ids": ";".join(card.get("chunk_ids") or []),
        "ingested_at": card.get("ingested_at", utc_now()),
    }
    append_csv_row(ledger_path, row, fieldnames=LEDGER_FIELDS)
    return row


def _match_any(value: str, keyword: str) -> bool:
    kw = keyword.strip().lower()
    if not kw:
        return False
    return kw in value.lower()


def find_assets_by_entity(
    assets: List[dict],
    keyword: str,
    limit: int = 10,
) -> List[dict]:
    """按业务标签/实体/文件名检索资产。"""
    matched: List[dict] = []
    for asset in assets:
        haystack = " ".join([
            str(asset.get("source_file", "")),
            str(asset.get("business_tags", "")),
            str(asset.get("entities", "")),
            str(asset.get("doc_type", "")),
        ])
        if _match_any(haystack, keyword):
            matched.append(asset)
    return matched[: max(1, limit)]
