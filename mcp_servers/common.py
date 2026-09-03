"""MCP 服务共享工具（纯标准库）。"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, List


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path: Path) -> List[dict]:
    out: List[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL 解析失败 {path}:{line_no}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL 每行必须是对象 {path}:{line_no}")
            out.append(obj)
    return out


def load_csv_rows(path: Path) -> List[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_rows(path: Path) -> List[dict]:
    if path.suffix.lower() == ".jsonl":
        return load_jsonl(path)
    if path.suffix.lower() == ".csv":
        return load_csv_rows(path)
    raise ValueError(f"不支持的台账格式: {path.suffix}")


def append_csv_row(path: Path, row: dict, fieldnames: Iterable[str] | None = None) -> None:
    """向 CSV 追加一行；文件不存在时新建。"""
    ensure_dir(path.parent)
    path_exists = path.exists()
    if fieldnames is None:
        fieldnames = list(row.keys()) if not path_exists else None
    if fieldnames is None:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = list(reader.fieldnames or row.keys())
    mode = "a" if path_exists else "w"
    with path.open(mode, newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if not path_exists:
            writer.writeheader()
        writer.writerow(row)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

