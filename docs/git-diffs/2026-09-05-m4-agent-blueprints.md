# Git Diff 总结：M4 T4.3 智能体编排蓝图与自检配置

- 日期：2026-09-05
- 里程碑：M4 检索-推理协同执行流，子任务 T4.3

## 涉及文件

### 新增

- `agents/blueprints.json`：主智能体 + 3 个协作智能体的编排蓝图（prompts/工具/知识库/协作/运行策略/发布标记）
- `agents/README.md`：蓝图用途与平台导入说明
- `scripts/validate_agent_blueprints.py`：蓝图结构校验 CLI
- `tests/test_agent_blueprints.py`：3 项校验测试（TDD）

### 修改

- `README.md`：T4.3 状态与里程碑同步

## 变更要点

1. `quality_decision` 启用规划模式、自检、会话 Metadata，并绑定三类知识库、图谱/证据链工具与 `evidence-decision` Skill。
2. 三个协作智能体（资产认知员/图谱运营官/证据审计官）与主智能体引用一致、无孤儿引用。
3. 校验器确保唯一主智能体、必填字段与协作引用合法。

## 测试与验收

- 全量 59 项 `unittest` 通过（新增 3 项）。
- `scripts/validate_agent_blueprints.py` 输出 `ok: true`。

## 注意事项 / 影响

- 蓝图以平台导出格式为权威；真实上线需在 Nexent Agent 配置页完成模型/工具绑定后导出。
