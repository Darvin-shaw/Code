# agents/ 智能体编排蓝图

`blueprints.json` 定义衡策 EvoNex 的智能体编排（草案）：

- `quality_decision`：主智能体，启用规划/自检/元数据，绑定三个知识库、图谱与证据链工具、`evidence-decision` Skill；
- `asset_cognition_assistant`：资产认知员；
- `ontology_steward`：图谱运营官；
- `evidence_auditor`：证据审计官。

校验命令：

```powershell
python scripts\validate_agent_blueprints.py
```

> Nexent 平台导入请使用平台导出的 JSON/ZIP 作为权威格式；本蓝图用于设计评审与字段对齐。
