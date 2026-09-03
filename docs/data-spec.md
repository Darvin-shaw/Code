# T1.1 数据规格与实体映射（v1）

> 适用模块：M1 场景与数据工程。数据全部为“衡星精工”虚构企业合成数据，统一由
> `scripts/generate_synthetic_data.py` 生成，任何引用该数据的测试与智能体配置都以本文件为唯一口径。

## 1. 数据范围与产品主体

演示主体为“衡星精工（HengXing Precision）”的两类产品：

- 产品 `AX-A`：电机轴 A 型（轴类零件）
- 产品 `GB-G1`：齿轮箱 G1 型（部件）

## 2. 实体与编码规则

所有主数据 ID 使用稳定编码，字母大写、数字定长，避免歧义：

| 实体 | 编码规则 | 示例 | 说明 |
|---|---|---|---|
| 产品/零件 | `{PRD}-{SEQ}` | `AX-A`、`GB-G1` | 产品主数据 |
| 批次 | `{PRD}-{YYYYMMDD}-{NN}` | `AX-20250518-01` | 同产品同日多批用 01/02… |
| 工序 | `{PROC}-{PRD}` | `HT-AX`（淬火回火）、`MC-AX`、`AS-GB` | 工序主数据 |
| 设备 | `{EQ}-{NN}` | `HT-03`（3 号热处理炉）、`MC-07`、`TF-02` | 设备主数据 |
| 检验/测量项 | `{ITEM}-{NN}` | `HARD-HRC`、`STRAIGHT-MM`、`NOISE-DB` | 测量项主数据 |
| 缺陷/不良类型 | `{DEF}-{NN}` | `DEF-HARD-LOW`、`DEF-STRAIGHT`、`DEF-SCRATCH` | 缺陷代码 |
| 内部文件 | `QP-{NNN}` / `WI-{NNN}` / `SP-{NNN}` | `QP-INC-03`（不合格品控制程序） | 规程/规范文件 |
| 标准条款锚点 | `STD:{章节/条款}` | `STD:GB/T19001:8.7` | 仅作为“概念锚点”，内容是自编摘要 |

跨文件必须通过上述 ID 互相引用，例如检验记录中的批次、产品、设备、测量项、缺陷类型均为主数据主键。

## 3. 生成目录与文件清单

生成根目录：`data/generated/`

```text
data/generated/
├─ 01_master_data/           # 主数据
│  ├─ products.csv
│  ├─ equipment.csv
│  ├─ processes.csv
│  ├─ measurement_items.csv
│  ├─ defect_codes.csv
│  └─ personnel.csv
├─ 02_quality_docs/          # 文本类：规程/规范/标准摘要（Markdown）
│  ├─ QP-INC-03-不合格品控制程序.md
│  ├─ WI-HT-AX-热处理作业指导书.md
│  ├─ WI-MC-AX-精加工作业指导书.md
│  ├─ SP-INSP-AX-电机轴检验规范.md
│  └─ STD-GB-T19001-摘要.md
├─ 03_quality_records/       # 表格类：检验/SPC/维保/不良品台账
│  ├─ spc_hardness_axis_202505.csv
│  ├─ inspection_records_2025H1.csv
│  ├─ nonconformity_records.csv
│  ├─ maintenance_logs.csv
│  └─ customer_complaints.csv
├─ 04_visual_evidence/       # 图片类：控制图/曲线/示意（生成器环境支持时输出）
│  ├─ spc_hardness_HT03_202505.png
│  ├─ oven_temperature_HT03_202505.png
│  └─ hardness_profile_schematic.png
├─ assets_ledger.csv         # 资产台账（资产卡片汇总）
└─ manifest.json             # 生成参数与文件清单
```

## 4. 关联规则（生成器必须保持一致性）

### 4.1 主时间线（黄金场景）

1. `AX-20250518-01` 批次在 2025-05-18 热处理后首检发现表面硬度偏低，共 **42 件**不合格。
2. 同期 SPC 台账中，3 号热处理炉（`HT-03`）自 2025-05-12 起连续出现过程均值下移，
   05-18 起连续 3 个点越过 2σ 下控制限——这是“过程失控证据”。
3. 维保记录显示：`HT-03` 热电偶在 2025-05-11 起处于“校准超期”待处理状态，
   05-20 才完成更换并恢复正常。
4. 客户投诉于 2025-06 出现 1 例齿轮箱异响（`GB-G1` 装配批次），与轴类硬度问题的
   设备/批次链条应可区分，避免 Demo 题互相污染。
5. 文档《不合格品控制程序 QP-INC-03》给出处置路径：返工 → 重新检验 → 让步接收需客户书面同意；
   检验规范给出硬度判据 `HARD-HRC: 48–56`。

### 4.2 一致性约束

- 5 月 18 日之后硬度 SPC 数据均值下降、不合格批次号必须能关联到 `HT-03`。
- 5 月 12 日前（校准超期前）没有硬度系统性偏低。
- 返工批次重新检验通过后，非同一批次的后续数据恢复正常。
- 除硬度偏低外，直线度、粗糙度数据保持正常范围，避免结论可被多条缺陷解释。

## 5. 文件 Schema 摘要

### 5.1 spc_hardness_axis_202505.csv

| 列 | 示例 | 说明 |
|---|---|---|
| sample_no | `AX-20250518-01-037` | 样本号 |
| batch_id | `AX-20250518-01` | 批次主键 |
| part_no | `AX-A` | 产品 |
| process_code | `HT-AX` | 工序 |
| equipment_code | `HT-03` | 设备 |
| item_code | `HARD-HRC` | 测量项 |
| measured_at | `2025-05-18 14:22` | 时间 |
| value | `46.2` | 实测值 |
| spec_low / spec_high | `48` / `56` | 规格限 |
| result | `NG` | OK/NG |
| chart_ref | `spc_hardness_HT03_202505.png` | 可视化引用 |

### 5.2 nonconformity_records.csv

| 列 | 示例 | 说明 |
|---|---|---|
| nc_id | `NC-20250518-001` | 不合格单号 |
| batch_id | `AX-20250518-01` | 批次 |
| qty | `42` | 数量 |
| defect_code | `DEF-HARD-LOW` | 缺陷 |
| found_process | `HT-AX` | 发现工序 |
| finding_ref | `WI-HT-AX/5.3` | 文件条款锚点 |
| disposition | `返工` | 处置动作 |
| status | `Reworked` | 状态 |

## 6. Golden 决策链（与评测集同源）

### 6.1 链 A：硬度不合格根因（多跳 + 数值 + 图表）

问题：`2025-05 AX-20250518-01 批次硬度不合格，是否与 3 号热处理炉温漂相关？`

证据步：

1. 检验记录/SPC：该批 `NG` 且 42 件不合格（文件：SPC/检验记录）；
2. 控制图：05-12 后过程均值下移、05-18 起连续越 2σ（文件：图表）；
3. 维保记录：`HT-03` 热电偶校准超期、05-20 更换（文件：维保台账）；
4. 工艺规程：硬度由淬火回火决定、设备与产品关联（文件：WI-HT-AX）；
5. 结论：高度相关，根因方向为热处理过程失控；需返工并按 QP-INC-03 复检。

### 6.2 链 B：不合格品处置决策

问题：`该 42 件是否允许让步接收？`

证据步：

1. 判据：`HARD-HRC 48–56`，实测低于下限（检验规范 + SPC）；
2. 程序：返工/报废/让步接收条件与审批路径（QP-INC-03）；
3. 合同/客诉记录：客户此前对同类产品无书面让步授权（台账/文件）；
4. 结论：默认不可让步；可返工后复检，若仍不合格需客户书面批准并报质量负责人。

## 7. 交付与验收

- 交付物：本规格 + 生成器 + 生成产物 + `assets_ledger.csv`。
- 验收：按 4.2 约束编写一致性测试；随机抽查 20 个资产卡片关键字段准确率 ≥90%。
