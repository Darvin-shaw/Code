"""T3.3 本体候选审核闭环 CLI（离线可跑）。

从候选三元组 JSONL 读取，按置信度策略自动分流：
高置信自动确认、低置信自动驳回、中间档进入人工审核表。

用法:
    python scripts/ontology_review.py --dry-run
    python scripts/ontology_review.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ontology.review_core import apply_policy, render_review_sheet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = PROJECT_ROOT / "ontology" / "candidates" / "candidate-triples.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "ontology" / "reviewed"


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--auto-confirm", type=float, default=0.9)
    parser.add_argument("--auto-reject", type=float, default=0.4)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    candidates = load_jsonl(Path(args.candidates))
    confirmed, rejected, pending = apply_policy(
        candidates,
        confirm_threshold=args.auto_confirm,
        reject_threshold=args.auto_reject,
    )
    summary = {
        "input": str(Path(args.candidates)),
        "total": len(candidates),
        "confirmed": len(confirmed),
        "rejected": len(rejected),
        "pending": len(pending),
        "auto_confirm_threshold": args.auto_confirm,
        "auto_reject_threshold": args.auto_reject,
    }
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False))
        return 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "confirmed-triples.jsonl", confirmed)
    write_jsonl(output_dir / "rejected-triples.jsonl", rejected)
    write_jsonl(output_dir / "pending-triples.jsonl", pending)
    (output_dir / "review-sheet.md").write_text(
        render_review_sheet(pending), encoding="utf-8")
    (output_dir / "review-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
