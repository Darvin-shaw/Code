# Git Diff 总结：M3 T3.1 本体 Schema v1 与种子三元组

- 日期：2026-09-03
- 里程碑：M3 本体与低资源构建，子任务 T3.1

## 涉及文件

### 新增

- `ontology/schema-v1.json`：12 个类、14 条关系及三元组属性约束（confidence/status/source/standard_ref/version）
- `ontology/standards-map.json`：GB/T 19001 概念摘要锚点（8.5/8.6/8.7）与内部文件/本体术语映射
- `ontology/seed-triples.jsonl`：25 条种子三元组（confirmed/candidate 分级，均带来源文件锚点）
- `tests/test_ontology_schema.py`：Schema 完整性、种子一致性、标准引用、GraphStore 可加载性测试

### 修改

- `README.md`：里程碑状态与测试数量同步（27 项单测通过）

## 变更要点

1. 本体覆盖产品/批次/工序/设备/检验记录/维保记录/缺陷/质量文件/标准条款/处置决策/人员，贴合制造质量场景。
2. 关系方向由 Schema 显式约束（subject_types/object_types），为后续一致性检查与审核闭环提供机器可校验基础。
3. 种子三元组既含 high-confidence confirmed 链（硬度批次→热处理→HT-03→维保/检验→缺陷→处置→文件），
   也保留 candidate 供 T3.2/T3.3 演示人工审核与增量更新。
4. 标准映射只使用自编摘要锚点，避免整篇转载；每个三元组可回到 `file_ref` 指向的合成语料。

## 测试与验收

- 27 项 `unittest` 全部通过（新增 6 项本体测试）。
- 种子三元组可整体载入 GraphStore（内存库）并检索，Schema 校验全部通过。

## 注意事项 / 影响

- 本阶段为“半自动构建”的骨架输入：T3.2 候选抽取将把新文档文本与 Schema 对接，candidate 状态用于人工确认闭环。
- 若后续引入 Neo4j，Schema 与三元组 JSONL 格式可保持不变，仅替换存储适配层。
