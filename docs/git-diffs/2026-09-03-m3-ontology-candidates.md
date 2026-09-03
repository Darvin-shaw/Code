# Git Diff 总结：M3 T3.2 候选抽取管线

- 日期：2026-09-03
- 里程碑：M3 本体与低资源构建，子任务 T3.2

## 涉及文件

### 新增

- `scripts/ontology_candidates.py`：规则驱动的本体候选抽取器（文档引用/标准对齐、检验与维保台账、主数据工序-设备）
- `ontology/candidates/candidate-triples.jsonl`：抽取结果（confirmed=5、candidate=4，均不与种子重复）
- `ontology/candidates/extraction-report.json`：抽取统计报告
- `tests/test_ontology_candidates.py`：Schema 合规、不重复种子、状态覆盖、可载入图谱测试

### 修改

- `README.md`：T3.2 完成状态与测试数量同步

## 变更要点

1. 抽取采用“规则通道 + LLM 预留通道”的低资源设计：规则负责稳定关系，LLM 通道接口已预留（`extract_candidates_with_llm`）。
2. 从文档显式引用、standards-map、检验/维保/不良品台账、主数据提取候选三元组；已在种子中的事实自动跳过。
3. 修复文档 ID 解析（`WI-HT-AX-热处理…` 此前会被误截为 `WI`），对齐后候选数量与内容符合预期。
4. 候选输出携带 confidence/status/source/file_ref/standard_ref，可直接进入 T3.3 人工审核闭环。

## 测试与验收

- 31 项 `unittest` 全部通过（新增 4 项 T3.2 测试）。
- dry-run 与实际生成均可复现：实际输出 9 条新事实/候选，Schema 校验通过。

## 注意事项 / 影响

- `ontology/candidates/` 为规则抽取产物，后续接入 LLM 后可扩展召回；审核通过后由 T3.3 写入图谱。
- 本阶段仍不依赖 Nexent/模型 API，可在离线环境独立复现。
