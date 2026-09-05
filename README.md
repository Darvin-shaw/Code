# 衡策 EvoNex — 可进化的制造质量决策智能体

基于华为 ModelEngine **Nexent** 的领域资产认知与决策智能体（赛事/开源项目）。目标是把先进制造企业里沉睡的
PDF 规程、Excel/CSV 台账、质检图片等异构存量数据，加工成「有 ID、有图谱、可检索、可推理、可追溯、可进化」
的决策资产，并在 Nexent 平台上完成检索-推理双驱动执行流与 Skill 沉淀。

## 当前开发状态

**Iteration 1（工程基础 + M1 数据工程 + M3 本体种子）**

**Iteration 2（M2 平台接入代码层 + M3 本体种子）进行中**

- [x] 项目骨架与开发规范
- [x] T1.1 数据规格文档与实体映射
- [x] T1.2 合成数据生成器（CSV=12、MD=5、PNG=3，可复现）
- [x] T1.3 资产卡片 Schema、台账格式与校验（8 项单测通过）
- [x] T1.4 Golden 评测集 v1（10 条）与评测 Harness
- [x] T2.3 MCP Server 核心逻辑与单测（资产认知/图谱本体/决策证据链）
- [x] T3.1 本体 Schema v1、标准锚点映射与 25 条种子三元组（27 项单测通过）
- [x] T3.2 规则驱动候选抽取管线（31 项单测通过，输出 9 条新事实/候选）
- [x] T3.3 候选审核闭环（自动分流 + 人工审核表，41 项单测通过）
- [x] T3.4 标准对齐与漂移报告（47 项单测通过）
- [x] T4.1 检索路由与查询分解（新增 7 项测试，全量 54 项）
- [x] T4.2 证据链决策工作流与 `evidence-decision` Skill（新增 2 项测试，全量 56 项）
- [x] T4.3 智能体编排蓝图与自检配置（新增 3 项测试，全量 59 项）
- [x] T2.1 部署文档、环境模板与就绪检查（实际启动阻塞：本机无 Docker）
- [x] T2.1 Nexent 实例启动（v2.4.1，大陆镜像源，Web http://localhost:3000 返回 200）
- [ ] T2.1 模型接入（需模型 API Key：LLM/VLM/Embedding）
- [x] T2.2 知识库规划、KB manifest 与表格摘要工具（34 项单测通过）
- [ ] Nexent MCP 联调与 Skill 包完善
- [ ] T3.3 人工审核闭环

## 目录结构

```text
.
├─ docs/                  # 方案、数据规格、开发规范等
├─ data/                  # 数据说明与静态样例
├─ scripts/               # 数据生成等可执行脚本
├─ ontology/              # 本体 Schema、种子三元组、标准映射
├─ tests/                 # Golden 集、Schema、MCP 核心与一致性测试
├─ mcp_servers/           # 自建 MCP 服务（核心逻辑 + FastMCP 包装）
├─ skills/                # 自建 Nexent Skill 包
├─ deploy/                # Nexent 部署与模型接入说明
├─ AGENTS.md              # 仓库提交约定
└─ requirements*.txt
```

## 本地快速开始

环境要求：Python 3.12+（当前无第三方硬依赖即可完成数据/校验）。

```powershell
# 1) 生成合成语料（会写入 data/generated/，默认含 CSV/Markdown；可选 matplotlib 图片）
python scripts\generate_synthetic_data.py

# 2) 只读自检（Schema、本体一致性、Golden 集格式）
python -m unittest discover -s tests -v
```

> 当前终端沙箱对“通过子进程写盘”有限制；若运行第 1 步提示权限问题，请在本机终端直接执行，
> 或批准提权后由助手代为执行。

## 文档地图

- 总体方案：[docs/2026-nexent-evolvable-agent-plan.md](docs/2026-nexent-evolvable-agent-plan.md)
- 开发与项目管理规范：[docs/development-conventions.md](docs/development-conventions.md)
- 数据规格与实体映射：[docs/data-spec.md](docs/data-spec.md)
- Nexent 部署清单：[deploy/nexent-deploy-checklist.md](deploy/nexent-deploy-checklist.md)
- 本体 Schema：`ontology/schema-v1.json`
- Golden 评测集：`tests/golden/golden_qa_v1.json`

## 里程碑（当前迭代）

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M1 | 场景数据、资产卡片、Golden 评测集 | 已完成 |
| M2 | Nexent 部署、知识库、MCP 接入 | 部署成功、知识库准备完成；模型接入/MCP 联调待 Key 与平台 |
| M3 | 本体 Schema/种子/候选抽取/审核闭环/标准对齐 | M3 全部完成 |
| M4 | 检索-推理执行流、Skills、智能体编排 | T4.1/T4.2/T4.3 完成 |
| M3 | 本体 v1、候选抽取、人工审核闭环 | 骨架完成 |
| M4 | 检索-推理执行流、证据链 | 待开发 |
| M5 | 评测回归与版本演化 | 待开发 |
| M6 | 开源仓库与路演 | 待开发 |
