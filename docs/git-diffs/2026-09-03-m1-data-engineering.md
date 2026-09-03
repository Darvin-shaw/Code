# Git Diff 总结：M1 场景与数据工程

- 日期：2026-09-03
- 里程碑：M1（T1.1 数据规格、T1.2 合成数据生成器、T1.3 资产卡片 Schema、T1.4 Golden 评测集）

## 涉及文件

### 新增（项目骨架与规范）

- `README.md`：项目说明、当前状态、目录结构、里程碑表
- `.gitignore`：忽略 `data/generated/`、虚拟环境、本地配置等
- `requirements.txt` / `requirements-dev.txt`：运行依赖清单
- `docs/development-conventions.md`：开发与项目管理规范（WBS、分支/提交、代码、DoD、文档）

### 新增（数据规格与工具）

- `docs/data-spec.md`：T1.1 实体编码、生成目录、关联规则、文件 Schema、两条 Golden 决策链
- `scripts/generate_synthetic_data.py`：T1.2 合成数据生成器（固定种子、标准库优先、可选 matplotlib）
- `scripts/README.md`：脚本说明
- `data/README.md`：数据目录约定

### 新增（资产卡片与评测）

- `data/asset_card_schema.json`：资产卡片 JSON Schema v1
- `data/static/asset_card.example.json`：资产卡片样例
- `tests/golden/golden_qa_v1.json`：T1.4 Golden 评测集（10 条）
- `tests/run_eval.py`：评测 Harness 骨架（只读校验）
- `tests/__init__.py`、`test_asset_cards.py`、`test_golden_set.py`、`test_generated_data.py`

### 既有

- `docs/2026-nexent-evolvable-agent-plan.md`：总体方案（上一轮已加入，本批随代码一并入库）

## 变更要点

1. 以“衡星精工”为背景落地 M1 数据工程：产品/批次/工序/设备/测量项/缺陷全链路主数据编码统一。
2. 生成器内置黄金情节：`AX-20250518-01` 批次 42 件硬度不合格，关联 `HT-03` 热电偶校准超期与 05-20 更换，具备多跳推理与反证区分度。
3. 资产卡片定义统一格式（Asset ID / 模态 / 类型 / 标签 / 实体 / SHA-256 / 入库时间），台账可由生成器自动产出。
4. Golden 评测集覆盖根因、处置、数值、文档定位、反证、多模态 6 类问题，并为每条标注必要/禁止证据与证据链。
5. 12 项 `unittest` 全部通过（Schema、Golden 格式、生成产物一致性）。

## 注意事项 / 影响

- `data/generated/` 为生成产物，按 `.gitignore` 不入库；新环境执行
  `python scripts/generate_synthetic_data.py` 即可复现（csv=12、md=5、png=3、资产台账 19 条）。
- 本阶段未含 Nexent 部署与本体/智能体实现，属于 M1 独立可交付成果。
- 图型生成依赖 matplotlib；无该依赖时生成器自动跳过图片，不影响表格与文档产物。
