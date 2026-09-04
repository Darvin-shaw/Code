"""T3.4 标准对齐与漂移报告 CLI。

读取当前标准映射与更新增量，输出新增/删除条款、受影响文档与三元组。

用法:
    python scripts/ontology_standard_drift.py --dry-run
    python scripts/ontology_standard_drift.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ontology.standard_alignment import apply_delta, build_drift_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = PROJECT_ROOT / "ontology" / "standards-map.json"
DELTA_PATH = PROJECT_ROOT / "ontology" / "updates" / "standard-update-2026.json"
TRIPLE_SOURCES = [
    PROJECT_ROOT / "ontology" / "seed-triples.jsonl",
    PROJECT_ROOT / "ontology" / "candidates" / "candidate-triples.jsonl",
    PROJECT_ROOT / "ontology" / "reviewed" / "confirmed-triples.jsonl",
]
REPORT_PATH = PROJECT_ROOT / "ontology" / "reports" / "standard-drift-report.json"


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl_many(paths: List[Path]) -> List[dict]:
    rows: List[dict] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=str(MAP_PATH))
    parser.add_argument("--delta", default=str(DELTA_PATH))
    parser.add_argument("--output", default=str(REPORT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    previous = load_json(Path(args.map))["mappings"]
    delta = load_json(Path(args.delta))
    updated = apply_delta(previous, delta)
    triples = load_jsonl_many(TRIPLE_SOURCES)
    report = {
        "delta_version": delta.get("version"),
        "title": delta.get("title"),
        **build_drift_report(previous, updated, triples),
    }
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False))
        return 0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
