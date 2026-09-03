"""T3.2 本体候选抽取管线（低资源，规则驱动 + 预留 LLM 通道）。

输入：合成资产（质量文档 / 检验与维保台账 / 主数据 / 标准映射）。
输出：与 `ontology/schema-v1.json` 合规、带 confidence/status/source/file_ref 的候选三元组。

设计说明：
- 规则通道用于稳定抽取“文档引用、工序-设备、检验-缺陷、批次-设备、处置-缺陷”等低风险关系；
- LLM 通道在 `extract_candidates_with_llm` 预留（当前返回空，接入模型后启用）；
- 已在种子三元组中的事实不会重复输出，未收录的实体关系以 candidate 状态进入审核池。

用法:
    python scripts/ontology_candidates.py --dry-run
    python scripts/ontology_candidates.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "generated"
DOC_ROOT = DATA_ROOT / "02_quality_docs"
RECORD_ROOT = DATA_ROOT / "03_quality_records"
MASTER_ROOT = DATA_ROOT / "01_master_data"
ONTOLOGY_ROOT = PROJECT_ROOT / "ontology"
OUTPUT_DIR = ONTOLOGY_ROOT / "candidates"
DEFAULT_VERSION = "v1"

CODE_PATTERN = re.compile(
    r"(?:AX-A|GB-G1|HT-\d{2}|MC-\d{2}|GR-\d{2}|AS-\d{2}|TF-\d{2}|"
    r"HARD-HRC|STRAIGHT-MM|RA-UM|NOISE-DB|DEF-[A-Z-]+|"
    r"QP-[A-Z]{3}-\d{2,3}|WI-[A-Z-]+|SP-[A-Z]+-[A-Z]+|"
    r"IR-\d{8}-\d{2}|NC-\d{8}-\d{3}|MT-\d{8}-\d{2}|"
    r"CP-\d{8}-\d{2}|STD:[A-Z0-9/.:-]+)"
)
DOC_ID_PATTERN = re.compile(
    r"(?:QP-[A-Z]{3}-\d{2,3}|WI-[A-Z0-9]+-[A-Z0-9]+|"
    r"SP-[A-Z0-9]+-[A-Z0-9]+|STD-[A-Z0-9/.:-]+)"
)

DISP_MAP = {
    "返工": "DISP-REWORK",
    "报废": "DISP-SCRAP",
    "让步接收评审": "DISP-CONCESSION",
    "退回总装": "DISP-RETURN",
}


@dataclass
class ExtractionResult:
    triples: List[dict] = None

    def __post_init__(self) -> None:
        self.triples = []


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_seed_keys() -> set:
    seed_path = ONTOLOGY_ROOT / "seed-triples.jsonl"
    keys: set = set()
    if not seed_path.exists():
        return keys
    with seed_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            keys.add((obj["subject_id"], obj["predicate"], obj["object_id"]))
    return keys


def doc_id_of(path: Path) -> str:
    match = DOC_ID_PATTERN.search(path.stem)
    if not match:
        raise ValueError(f"无法从文件名识别文档 ID: {path.name}")
    return match.group(0)


def reference_doc_id(value: str) -> str:
    """从文本/锚点中提取文档 ID；缺省回退 QP-INC-03。"""
    matches = [m for m in CODE_PATTERN.findall(str(value))
               if m.startswith(("QP-", "WI-", "SP-"))]
    return matches[0] if matches else "QP-INC-03"


def code_refs(text: str) -> List[str]:
    return list(dict.fromkeys(m.group(0) for m in CODE_PATTERN.finditer(text)))


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def make_triple(subject_id: str, subject_type: str, predicate: str,
                object_id: str, object_type: str, source: str, file_ref: str,
                confidence: float = 0.55, status: str = "candidate",
                standard_ref: str = "") -> dict:
    return {
        "subject_id": subject_id,
        "subject_type": subject_type,
        "predicate": predicate,
        "object_id": object_id,
        "object_type": object_type,
        "confidence": round(float(confidence), 3),
        "status": status,
        "source": source,
        "standard_ref": standard_ref,
        "version": DEFAULT_VERSION,
        "file_ref": file_ref,
    }


def schema_of() -> dict:
    return load_json(ONTOLOGY_ROOT / "schema-v1.json")


def standards_mappings() -> List[dict]:
    return load_json(ONTOLOGY_ROOT / "standards-map.json")["mappings"]


def extract_doc_references() -> List[dict]:
    """文档间引用（文本显式引用）+ 文档对齐标准条款（以 standards-map 为准）。"""
    triples: List[dict] = []
    if not DOC_ROOT.exists():
        return triples
    docs = sorted(DOC_ROOT.glob("*.md"))
    doc_ids = {doc_id_of(d) for d in docs}
    for doc in docs:
        doc_id = doc_id_of(doc)
        text = doc.read_text(encoding="utf-8")
        rel = f"02_quality_docs/{doc.name}"
        for ref in code_refs(text):
            if ref == doc_id:
                continue
            if ref in doc_ids:
                triples.append(make_triple(
                    doc_id, "QualityDocument", "references", ref, "QualityDocument",
                    "rule-doc", rel, confidence=0.8, status="candidate"))

    for mapping in standards_mappings():
        clause = mapping["clause_id"]
        for internal_doc in mapping["internal_docs"]:
            if internal_doc in doc_ids:
                triples.append(make_triple(
                    internal_doc, "QualityDocument", "aligns_with", clause,
                    "StandardClause", "rule-standard-map", "",
                    confidence=0.85, status="candidate", standard_ref=clause))
    return triples


def extract_record_relations() -> List[dict]:
    """检验/不良品/维保台账中的可追溯关系。"""
    triples: List[dict] = []
    if not RECORD_ROOT.exists():
        return triples

    nc_path = RECORD_ROOT / "nonconformity_records.csv"
    if nc_path.exists():
        with nc_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                batch, defect = row["batch_id"], row["defect_code"]
                rel = "03_quality_records/nonconformity_records.csv"
                triples.append(make_triple(
                    batch, "Batch", "has_defect", defect, "Defect",
                    "rule-record", rel, confidence=0.9, status="confirmed"))
                decision = DISP_MAP.get(row.get("disposition", ""))
                if decision:
                    triples.append(make_triple(
                        decision, "DispositionDecision", "applies_to", defect,
                        "Defect", "rule-record", rel, confidence=0.85,
                        status="confirmed"))
                    triples.append(make_triple(
                        decision, "DispositionDecision", "based_on",
                        reference_doc_id(row.get("disposition_reason", "QP-INC-03")),
                        "QualityDocument", "rule-record", rel, confidence=0.8,
                        status="confirmed"))

    ir_path = RECORD_ROOT / "inspection_records_2025H1.csv"
    if ir_path.exists():
        with ir_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                rel = "03_quality_records/inspection_records_2025H1.csv"
                triples.append(make_triple(
                    row["batch_id"], "Batch", "inspected_by", row["record_id"],
                    "InspectionRecord", "rule-record", rel, confidence=0.95,
                    status="confirmed"))
                triples.append(make_triple(
                    row["record_id"], "InspectionRecord", "measures",
                    row["item_code"], "MeasurementItem", "rule-record", rel,
                    confidence=0.95, status="confirmed"))

    mt_path = RECORD_ROOT / "maintenance_logs.csv"
    if mt_path.exists():
        with mt_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                rel = "03_quality_records/maintenance_logs.csv"
                triples.append(make_triple(
                    row["equipment_code"], "Equipment", "has_maintenance",
                    row["maintenance_id"], "MaintenanceRecord", "rule-record",
                    rel, confidence=0.95, status="confirmed"))
    return triples


def extract_master_relations() -> List[dict]:
    """主数据中的工序-设备关系。"""
    triples: List[dict] = []
    process_path = MASTER_ROOT / "processes.csv"
    if process_path.exists():
        with process_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                rel = "01_master_data/processes.csv"
                equipment = row.get("key_equipment")
                if equipment:
                    triples.append(make_triple(
                        row["process_code"], "Process", "executed_on",
                        equipment, "Equipment", "rule-master", rel,
                        confidence=0.98, status="confirmed"))
    return triples


def dedupe_and_mark(rows: List[dict], seed_keys: set) -> List[dict]:
    """去重；若与种子一致则跳过，返回新候选/确认事实。"""
    out: List[dict] = []
    seen: set = set()
    for triple in rows:
        key = (triple["subject_id"], triple["predicate"], triple["object_id"])
        if key in seen or key in seed_keys:
            continue
        seen.add(key)
        out.append(triple)
    return out


def extract_candidates_with_llm(text: str, schema: dict) -> List[dict]:
    """LLM 通道预留：接入 OpenAI 兼容模型后可返回高召回候选。"""
    _ = (text, schema)
    return []


def run_extraction() -> List[dict]:
    schema = schema_of()
    seed_keys = load_seed_keys()
    all_rows: List[dict] = []
    all_rows += extract_doc_references()
    all_rows += extract_record_relations()
    all_rows += extract_master_relations()
    for path in sorted(DOC_ROOT.glob("*.md")):
        all_rows += extract_candidates_with_llm(path.read_text(encoding="utf-8"), schema)
    return dedupe_and_mark(all_rows, seed_keys)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR),
                        help="候选输出目录（默认 ontology/candidates）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只统计候选数量，不写盘")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys_argv())
    rows = run_extraction()
    if args.dry_run:
        confirmed = sum(1 for r in rows if r["status"] == "confirmed")
        candidate = sum(1 for r in rows if r["status"] == "candidate")
        rejected = sum(1 for r in rows if r["status"] == "rejected")
        print(f"[dry-run] 抽取候选总数={len(rows)} "
              f"(confirmed={confirmed}, candidate={candidate}, rejected={rejected})")
        return 0
    output_dir = Path(args.output_dir)
    candidate_path = output_dir / "candidate-triples.jsonl"
    write_jsonl(candidate_path, rows)
    report = {
        "total": len(rows),
        "confirmed": sum(1 for r in rows if r["status"] == "confirmed"),
        "candidate": sum(1 for r in rows if r["status"] == "candidate"),
        "rejected": sum(1 for r in rows if r["status"] == "rejected"),
        "output": str(candidate_path),
    }
    with (output_dir / "extraction-report.json").open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))
    return 0


def sys_argv() -> List[str]:
    import sys

    return sys.argv[1:]


if __name__ == "__main__":
    raise SystemExit(main())
