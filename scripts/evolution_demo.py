"""M5 T5.2 版本演化演示 CLI。

示例：v1 -> v2（引入 2026 标准对齐 + 审核确认三元组），回归门通过即可发布。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ontology.evolution_gate import evolution_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "ontology" / "reports" / "evolution-report.json"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(REPORT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    report = evolution_report(
        old_version="v1",
        new_version="v2",
        old_scores={"recall": 0.90, "precision": 0.80, "traceability": 0.95},
        new_scores={"recall": 0.92, "precision": 0.81, "traceability": 0.97},
        changes=["2026 标准条款对齐", "新增审核确认三元组", "修正 2 条旧决策"],
        tolerance=0.05,
    )
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
