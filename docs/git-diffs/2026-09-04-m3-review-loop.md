# Git Diff 总结：M3 T3.3 本体候选审核闭环

- 日期：2026-09-04
- 里程碑：M3 本体与低资源构建，子任务 T3.3

## 涉及文件

### 新增

- `ontology/__init__.py`：本体核心包入口
- `ontology/review_core.py`：三元组键、自动/人工分流、决策留痕、审核表渲染
- `scripts/ontology_review.py`：审核 CLI（dry-run + 落地 reviewed 产物）
- `ontology/reviewed/confirmed-triples.jsonl`、`pending-triples.jsonl`、`rejected-triples.jsonl`
- `ontology/reviewed/review-sheet.md`、`review-summary.json`
- `tests/test_ontology_review.py`：7 项审核闭环测试

### 修改

- `tests/test_golden_set.py`：改为包式导入，兼容不同 unittest discover 方式
- `README.md`：T3.3 完成状态同步

## 变更要点

1. 审核策略：置信度 ≥0.9 自动确认、<0.4 自动驳回、中间档进入人工审核表；
   决策写入 reviewer/reviewed_at/decision_reason 留痕。
2. CLI 可离线复现；dry-run 输出 9 条候选 → 5 confirmed、0 rejected、4 pending。
3. 确认/驳回/待审与审核表独立落盘，便于审计回放与后续写回图谱。

## 测试与验收

- 全量 41 项 `unittest` 通过（新增 7 项 T3.3 测试，TDD：先失败后实现）。
- 修复 unittest discover 路径兼容问题（run_eval 包式导入）。

## 注意事项 / 影响

- Nexent 平台内的人工审核交互待模型/平台配置后接入；当前产物为离线闭环。
