# Git Diff 总结：M5 T5.2 版本演化回归门与演示

- 日期：2026-09-05
- 里程碑：M5 进化闭环，子任务 T5.2

## 涉及文件

### 新增

- `ontology/evolution_gate.py`：指标对比、容差回归门、演化报告
- `ontology/reports/evolution-report.json`：v1→v2 演示报告
- `scripts/evolution_demo.py`：演化演示 CLI
- `tests/test_evolution_gate.py`：3 项回归门测试（TDD）

### 修改

- `README.md`：T5.2 状态与里程碑同步

## 变更要点

1. 回归门：任一受控指标（recall/precision/traceability）退化超过容差即禁止发布。
2. 演示场景：v1→v2 因“2026 条款对齐 + 审核三元组 + 修正旧决策”全部指标上升，门通过。

## 测试与验收

- 全量 69 项 `unittest` 通过（新增 3 项）。
- 演示报告输出 `passed: true`。

## 注意事项 / 影响

- 真实版本对比需接入模型评测结果；当前指标为示例口径。
