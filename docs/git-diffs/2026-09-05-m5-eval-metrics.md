# Git Diff 总结：M5 T5.1 离线评测指标与评分

- 日期：2026-09-05
- 里程碑：M5 进化闭环与模板沉淀，子任务 T5.1

## 涉及文件

### 新增

- `tests/eval_metrics.py`：证据召回/精确、反证违规、溯源完整度、单题聚合评分
- `tests/test_eval_metrics.py`：5 项指标测试（TDD）

### 修改

- `tests/run_eval.py`：新增 `score_results`，可对 Golden 结果文件逐题评分
- `README.md`：T5.1 状态与里程碑同步

## 变更要点

1. 建立“召回/精确/违规/可溯源”四类可比较指标，供版本 A/B 回归使用。
2. `score_results` 预留智能体输出接入点：结果格式为 `{qid: {retrieved, assertions_evidence}}`。

## 测试与验收

- 全量 66 项 `unittest` 通过（新增 5 项）。

## 注意事项 / 影响

- 答案正确率需接入真实模型后补充；证据链类指标已可离线评估。
