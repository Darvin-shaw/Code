"""T1.4 Golden 评测 Harness（骨架）。

当前里程碑只负责校验评测集与打印评测计划；接入智能体输出后，可在此实现：
答案正确率、证据召回/精确、溯源完整度、工具选择准确率、多跳深度等指标。

用法（只读，不产生任何文件）:
    python -B tests/run_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_KEYS = {
    "id", "type", "question", "gold_answer_summary",
    "required_evidence", "forbidden_evidence", "gold_chain",
}
SUPPORTED_TYPES = {
    "root-cause", "disposition", "numeric", "doc-lookup",
    "counter-evidence", "multimodal",
}


def load_golden(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("golden 集顶层必须是数组")
    return data


def validate_golden(data: list[dict]) -> list[str]:
    errors: list[str] = []
    ids = set()
    for idx, item in enumerate(data):
        missing = REQUIRED_KEYS - set(item)
        if missing:
            errors.append(f"[{idx}] 缺少字段: {sorted(missing)}")
            continue
        if item["id"] in ids:
            errors.append(f"重复 id: {item['id']}")
        ids.add(item["id"])
        if item["type"] not in SUPPORTED_TYPES:
            errors.append(f"{item['id']} 未知 type: {item['type']}")
        if not item["question"] or not item["gold_answer_summary"]:
            errors.append(f"{item['id']} question/gold_answer_summary 不能为空")
        if not item["required_evidence"]:
            errors.append(f"{item['id']} required_evidence 至少一条")
        if not isinstance(item.get("gold_chain"), list) or not item["gold_chain"]:
            errors.append(f"{item['id']} gold_chain 至少一步")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    golden_path = root / "tests" / "golden" / "golden_qa_v1.json"
    data = load_golden(golden_path)
    errors = validate_golden(data)
    if errors:
        print("评测集校验失败：")
        for err in errors:
            print(f"  - {err}")
        return 1

    by_type: dict[str, int] = {}
    for item in data:
        by_type[item["type"]] = by_type.get(item["type"], 0) + 1

    print(f"Golden 集校验通过：共 {len(data)} 条")
    for qtype, count in sorted(by_type.items()):
        print(f"  - {qtype}: {count}")
    print("评测计划：接入智能体输出后按证据链计算 答案正确率 / 证据召回 / 溯源完整度。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

