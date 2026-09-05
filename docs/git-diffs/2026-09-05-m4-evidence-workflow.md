# Git Diff 总结：M4 T4.2 证据链决策工作流与 Skill

- 日期：2026-09-05
- 里程碑：M4 检索-推理协同执行流，子任务 T4.2

## 涉及文件

### 新增

- `mcp_servers/decision_trace_server/evidence_workflow.py`：路由 + 证据链 + 校验 + 渲染编排
- `skills/evidence-decision/`：Nexent 官方格式 Skill 包
  - `SKILL.md`：触发场景、七步工作流、边界与错误处理
  - `config/schema.yaml` / `config/config.yaml`：top_k 与引用强约束参数
  - `examples.md`：让步接收与根因归因示例
- `tests/test_evidence_workflow.py`：2 项工作流测试（TDD）

### 修改

- `README.md`：T4.2 状态与里程碑同步

## 变更要点

1. 把已实现的检索路由与证据链核心串成可离线执行的工作流。
2. 提供符合 Nexent SKILL.md 规范的 `evidence-decision` 包，后续可直接上传/上架并绑定智能体。

## 测试与验收

- 全量 56 项 `unittest` 通过（新增 2 项）。
- 工作流可输出 route、traceable、issues、Markdown、Mermaid。

## 注意事项 / 影响

- Skill 尚未上传 Nexent（需模型/平台环境或管理员操作）；离线骨架与格式已完成。
