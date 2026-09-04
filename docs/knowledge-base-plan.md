# T2.2 知识库体系规划（Nexent）

## 1. 设计目标

- 按模态与业务语义分区，避免“一个知识库塞所有文件”导致的检索稀释；
- 表格/图片先做“结构化摘要化”预处理，再进入检索；
- 知识库摘要与用户组权限按角色设计，供智能体自主选择来源。

## 2. 三个知识库

| 知识库名称 | 内容 | 模态 | Embedding | 说明 |
|---|---|---|---|---|
| `标准规程库` | `02_quality_docs/*.md`（规程/规范/标准摘要） | text | 文本 embedding | 检索条款、处置程序、工艺要求 |
| `台账与记录库` | `01_master_data/*.csv`、`03_quality_records/*.csv`、`table_summaries/*.md` | table/text | 文本 embedding | 表格先转结构化摘要提升语义命中 |
| `图片证据库` | VLM 生成的“图片事实描述文本”（未来补充到该库） | text/image | 文本 embedding；若官方版本支持图片直接入库则启用 multi-embedding | 原图为附件证据，不假设可直接上传知识库 |

> Nexent 知识库名称要求仅中文或小写字母；名称中不含空格/斜杠。

## 3. 分块与摘要策略

- 标准规程库：按 Markdown 标题语义分块；重点条款（4.1 返工、4.3 让步等）保留整段。
- 台账库：CSV 不直接依赖切块——由 `scripts/load_knowledge_bases.py --build-summaries` 生成 `table_summaries/*.md`，
  再按表为单位入库，保留批次/设备/缺陷等主键便于图谱关联。
- 图片库：以官方“知识库上传支持格式”为准——PNG 未列入上传清单，因此先由 VLM 生成图片事实文本
  （控制图越限点、缺陷类别等）再入库；原图保留为工作区附件，在问答/报告阶段作为可视化证据引用。
- 每个知识库启用自摘要（建议 1 天），供智能体选择来源；文件更新后自动重新入库。

## 4. 权限建议

- `标准规程库`：质量/工艺组读写，其他用户组只读。
- `台账与记录库`：质量组读写，审核员只读。
- `图片证据库`：质量/售后组读写，演示账号只读。

## 5. 与资产台账/本体的关系

- `data/generated/assets_ledger.csv` 是资产目录，不入知识库，用于 MCP `asset_cognition_server` 检索。
- `ontology/` 三元组通过 `kg_ontology_server` 服务，作为知识库之外的“关系证据层”。
- 智能体执行流：向量/表格检索取候选事实 → 图谱检索取关联实体 → 证据链服务做溯源。

## 6. 检索效果验收（平台可用后）

- 10 条代表性查询 Hit@5 ≥ 0.8；
- QA-001/QA-002/QA-003/QA-009 等 Golden 问题能找回全部必备证据文件；
- 表格数值问题（如 42 件硬度范围）可命中对应台账摘要。

## 7. 官方依据（Nexent 使用以官方站点为准）

- 知识库配置（创建/上传格式/Embedding 类型/总结频率/Chunk）：
  https://modelengine-group.github.io/nexent/zh/user-guide/agent-development/knowledge-configuration.html
- Skill 仓库与 SKILL.md 规范（名称小写连字符、config/schema.yaml、两种技能类型、ZIP 结构）：
  https://modelengine-group.github.io/nexent/zh/user-guide/resource-repository/skill-repository.html
- 智能体开发与工具/Skill 绑定（含官方工具与运行策略）：
  https://modelengine-group.github.io/nexent/zh/user-guide/agent-development/agent-configuration.html
- 官方 Skill 列表：https://modelengine-group.github.io/nexent/zh/user-guide/resource-repository/official-skills.html
