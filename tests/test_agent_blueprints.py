"""M4 T4.3 智能体编排蓝图校验测试。"""

from __future__ import annotations

import unittest


class AgentBlueprintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from scripts.validate_agent_blueprints import load_blueprints

        cls.data = load_blueprints()

    def test_blueprints_include_main_and_collaborators(self) -> None:
        agents = {agent["variable"] for agent in self.data["agents"]}
        self.assertIn("quality_decision", agents)
        self.assertIn("asset_cognition_assistant", agents)
        self.assertIn("ontology_steward", agents)
        self.assertIn("evidence_auditor", agents)

    def test_collaborator_refs_resolve(self) -> None:
        from scripts.validate_agent_blueprints import validate_blueprints

        errors = validate_blueprints(self.data)
        self.assertEqual([], errors)

    def test_main_agent_enables_self_verification(self) -> None:
        main_agent = next(
            agent for agent in self.data["agents"]
            if agent["variable"] == "quality_decision")
        self.assertTrue(main_agent["publish_as_main"])
        self.assertTrue(main_agent["run_strategy"]["self_verification"])


if __name__ == "__main__":
    unittest.main()
