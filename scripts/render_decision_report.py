"""T4.4 生成决策溯源示例报告（离线可跑）。

用法:
    python scripts/render_decision_report.py --dry-run
    python scripts/render_decision_report.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_servers.decision_trace_server.decision_report import render_full_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = PROJECT_ROOT / "tests" / "golden" / "golden_qa_v1.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "sample-decision-report.md"


def load_golden() -> List[dict]:
    with GOLDEN_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-id", default="QA-002")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    item = next(q for q in load_golden() if q["id"] == args.golden_id)
    evidence = [
        {
            "evidence_id": f"E{idx}",
            "source_file": step["evidence"],
            "quote": step["step"],
            "role": "support",
        }
        for idx, step in enumerate(item["gold_chain"], 1)
    ]
    assertions = [
        {"text": step["step"], "evidence_ids": [f"E{idx}"],
         "conclusion": idx == len(item["gold_chain"])}
        for idx, step in enumerate(item["gold_chain"], 1)
    ]
    report = render_full_report(item["question"], assertions, evidence)
    if args.dry_run:
        print(f"[dry-run] golden={item['id']} output={args.output} chars={len(report)}")
        return 0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"written={output} chars={len(report)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
