# Git Diff 总结：M4 T4.1 检索路由与查询分解

- 日期：2026-09-05
- 里程碑：M4 检索-推理协同执行流，子任务 T4.1

## 涉及文件

### 新增

- `mcp_servers/decision_trace_server/retrieval_router.py`：问题分类（multimodal/numeric/doc-lookup/disposition/root-cause）、
  检索源优先级、证据执行计划、查询拆分
- `tests/test_query_router.py`：7 项 T4.1 测试（TDD，先失败后实现）

### 修改

- `README.md`：T4.1 状态与里程碑同步

## 变更要点

1. 用关键词加权顺序消歧：如“让步接收…依据是什么”走 disposition，而“条款依据出自哪个文件”走 doc-lookup。
2. 输出统一的 route 对象，供后续 MCP/智能体选择知识库与工具。
3. `evidence_plan` 固化“检索 → 推理 → 反证 → 校验 → 结论”双驱动步骤。

## 测试与验收

- 全量测试 54 项通过（新增 7 项）。
- dry-run/单测不依赖 Nexent 与模型。

## 注意事项 / 影响

- 路由规则后续可接入 Golden 集校准阈值；当前为可解释规则版本。
