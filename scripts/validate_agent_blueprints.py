"""M4 T4.3 智能体编排蓝图校验。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = PROJECT_ROOT / "agents" / "blueprints.json"

REQUIRED_AGENT_FIELDS = {
    "variable", "display_name", "role", "duty_prompt", "constraint_prompt",
    "knowledge_bases", "tools", "skills", "collaborative_agents",
    "run_strategy", "publish_as_main", "publish_as_a2a",
}
REQUIRED_RUN_FIELDS = {
    "planning_mode", "max_steps", "self_verification", "allow_conversation_metadata",
}


def load_blueprints(path: Path = BLUEPRINT_PATH) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_blueprints(data: dict) -> List[str]:
    """校验蓝图结构与协作引用；空列表表示合法。"""
    errors: List[str] = []
    agents = data.get("agents", [])
    variables = [agent.get("variable") for agent in agents]
    if len(variables) != len(set(variables)):
        errors.append("agent variable 存在重复")
    mains = [agent["variable"] for agent in agents if agent.get("publish_as_main")]
    if len(mains) != 1:
        errors.append(f"主智能体必须且仅有一个，实际: {mains}")
    for agent in agents:
        name = agent.get("variable", "<unknown>")
        missing = REQUIRED_AGENT_FIELDS - set(agent)
        if missing:
            errors.append(f"{name} 缺少字段: {sorted(missing)}")
            continue
        missing_run = REQUIRED_RUN_FIELDS - set(agent["run_strategy"])
        if missing_run:
            errors.append(f"{name} run_strategy 缺少字段: {sorted(missing_run)}")
        for ref in agent["collaborative_agents"]:
            if ref not in variables:
                errors.append(f"{name} 引用了不存在的协作智能体: {ref}")
    return errors


if __name__ == "__main__":
    data = load_blueprints()
    issues = validate_blueprints(data)
    print(json.dumps({"ok": not issues, "errors": issues}, ensure_ascii=False, indent=2))
