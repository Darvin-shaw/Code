"""T2.2 知识库准备工具（离线部分）。

职责：
1. 扫描 data/generated/，把文件归类为 Nexent 三个知识库；
2. 对 CSV 台账生成 Markdown 结构化摘要（提升表格检索命中）；
3. 输出 kb_manifest.json 供 Nexent 上线后的“上传→校验→验收”使用。

说明：Nexent 尚无公开的统一“本地文件导入”API 约定前，不冒充自动上传；
平台就绪后按 manifest 顺序在界面/官方 API 中导入即可。

用法:
    python scripts/load_knowledge_bases.py --dry-run
    python scripts/load_knowledge_bases.py --build-summaries
    python scripts/load_knowledge_bases.py --check
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "generated"

KB_CONFIG = [
    {
        "id": "kb_standard",
        "name": "标准规程库",
        "modality": "text",
        "summary": "工艺规程、检验规范、不合格品控制程序与标准要点摘要",
        "priority": 1,
    },
    {
        "id": "kb_records",
        "name": "台账与记录库",
        "modality": "table",
        "summary": "主数据、检验/SPC/维保/不良品台账及其表格摘要",
        "priority": 2,
    },
    {
        "id": "kb_visual",
        "name": "图片证据库",
        "modality": "image",
        "summary": "SPC 控制图、温度趋势与硬度剖面等视觉证据",
        "priority": 3,
    },
]


def rel_dir(rel: str) -> str:
    return rel.split("/")[0]


def classify_files(root: Path) -> Dict[str, List[dict]]:
    groups: Dict[str, List[dict]] = {cfg["id"]: [] for cfg in KB_CONFIG}
    if not root.exists():
        return groups
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        doc_type = path.suffix.lstrip(".").lower()
        if rel.startswith("02_quality_docs/"):
            groups["kb_standard"].append({
                "file": rel, "modality": "text", "doc_type": doc_type,
                "format": path.suffix.lstrip("."),
            })
        elif rel.startswith(("01_master_data/", "03_quality_records/")):
            groups["kb_records"].append({
                "file": rel, "modality": "table",
                "doc_type": "table_summary" if "table_summaries/" in rel else doc_type,
                "format": path.suffix.lstrip("."),
            })
        elif rel.startswith("04_visual_evidence/"):
            groups["kb_visual"].append({
                "file": rel, "modality": "image", "doc_type": doc_type,
                "format": path.suffix.lstrip("."),
                "ingest": False,
                "note": "PNG 不在官方知识库上传格式清单中，需先由 VLM 生成图片事实文本入库",
            })
    return groups


def numeric_stats(rows: List[dict], columns: List[str]) -> Dict[str, dict]:
    stats: Dict[str, dict] = {}
    for col in columns:
        values: List[float] = []
        for row in rows:
            try:
                values.append(float(str(row[col]).replace(",", "")))
            except (KeyError, ValueError):
                continue
        if values:
            stats[col] = {
                "min": min(values), "max": max(values),
                "avg": round(sum(values) / len(values), 3), "count": len(values),
            }
    return stats


def unique_values(rows: List[dict], column: str, limit: int = 8) -> List[str]:
    out: List[str] = []
    for row in rows:
        value = str(row.get(column, "")).strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def build_table_summaries(root: Path) -> List[str]:
    """为台账 CSV 生成 Markdown 摘要，返回新生成的相对路径列表。"""
    records_dir = root / "03_quality_records"
    target_dir = records_dir / "table_summaries"
    target_dir.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for csv_path in sorted(records_dir.glob("*.csv")):
        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        columns = list(rows[0].keys())
        lines = [
            f"# 表格摘要：{csv_path.name}",
            "",
            f"- 源文件：{csv_path.name}",
            f"- 记录数：{len(rows)}",
            f"- 列：{', '.join(columns)}",
            "",
            "## 关键业务键",
            "",
        ]
        for col in ("batch_id", "equipment_code", "defect_code", "record_id",
                    "nc_id", "maintenance_id", "status"):
            if col in columns:
                values = unique_values(rows, col)
                lines.append(f"- {col}：{', '.join(values) or '无'}")
        numeric_columns = [c for c in columns if c in {
            "value", "qty", "ng_qty", "sample_size", "spec_low", "spec_high"}]
        if numeric_columns:
            lines.extend(["", "## 数值概览", ""])
            for col, stats in numeric_stats(rows, numeric_columns).items():
                lines.append(
                    f"- {col}: min={stats['min']}, max={stats['max']}, "
                    f"avg={stats['avg']}, n={stats['count']}")
        lines.extend([
            "",
            "> 说明：此摘要由 T2.2 工具生成，用于提升表格语义检索，不代表替换原始台账。",
            "",
        ])
        target = target_dir / (csv_path.stem + ".md")
        target.write_text("\n".join(lines), encoding="utf-8")
        written.append(target.relative_to(root).as_posix())
    return written


def build_manifest(root: Path, with_summaries: bool = False) -> dict:
    if with_summaries and root.exists():
        build_table_summaries(root)
    groups = classify_files(root)
    knowledge_bases = []
    for cfg in KB_CONFIG:
        files = sorted(groups[cfg["id"]], key=lambda x: x["file"])
        knowledge_bases.append({
            **cfg,
            "file_count": len(files),
            "files": files,
            "chunk_strategy": {
                "kb_standard": "按 Markdown 标题语义分块",
                "kb_records": "优先入库表格摘要，保留原始 CSV 作为附件",
                "kb_visual": "图片事实文本化 + 原图多模态向量化",
            }[cfg["id"]],
            "summary_schedule": "1 天",
        })
    return {
        "version": "v1",
        "generated_at": "",
        "data_root": "data/generated",
        "knowledge_bases": knowledge_bases,
        "total_files": sum(kb["file_count"] for kb in knowledge_bases),
    }


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DATA_ROOT),
                        help="数据根目录（默认 data/generated）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印分类统计")
    parser.add_argument("--build-summaries", action="store_true",
                        help="生成 CSV 表格摘要")
    parser.add_argument("--check", action="store_true",
                        help="校验 kb_manifest.json 指向的文件是否存在")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    import sys

    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.output_dir)
    manifest = build_manifest(root, with_summaries=args.build_summaries)

    if args.dry_run:
        print(f"[dry-run] 知识库分类：")
        for kb in manifest["knowledge_bases"]:
            print(f"  {kb['name']}: {kb['file_count']} 文件")
        return 0

    if args.check:
        errors = []
        for kb in manifest["knowledge_bases"]:
            for item in kb["files"]:
                if not (root / item["file"]).exists():
                    errors.append(f"{kb['id']}: {item['file']} 缺失")
        print(json.dumps({"ok": not errors, "errors": errors},
                         ensure_ascii=False, indent=2))
        return 0 if not errors else 1

    output = root / "kb_manifest.json"
    with output.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(json.dumps({
        "ok": True,
        "manifest": str(output),
        "knowledge_bases": {kb["name"]: kb["file_count"]
                            for kb in manifest["knowledge_bases"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
