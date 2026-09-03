"""衡策 EvoNex T1.2 合成数据生成器。

以“衡星精工”为背景生成可复现的多模态合成语料（主数据 / 质量文档 / 检验与
SPC 台账 / 维保与客诉记录 / 可视化证据 / 资产台账），供 Nexent 知识库导入、
本体抽取与评测使用。

用法:
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --output-dir data/generated --dry-run

核心逻辑仅使用标准库；matplotlib 可用时额外生成 PNG 图表，否则跳过并写入说明。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


GENERATOR_VERSION = "0.1.0"
DEFAULT_SEED = 20250903
INGESTED_AT = "2026-09-03T00:00:00Z"


# ---------------------------------------------------------------------------
# 主数据目录
# ---------------------------------------------------------------------------
PRODUCTS = [
    {"part_no": "AX-A", "name": "电机轴 A 型", "product_type": "轴类零件",
     "primary_processes": "HT-AX;MC-AX;GR-AX"},
    {"part_no": "GB-G1", "name": "齿轮箱 G1 型", "product_type": "部件",
     "primary_processes": "AS-GB"},
]

PROCESSES = [
    {"process_code": "HT-AX", "product_part": "AX-A", "name": "淬火回火（热处理）",
     "key_equipment": "HT-03"},
    {"process_code": "MC-AX", "product_part": "AX-A", "name": "数控精车",
     "key_equipment": "MC-07"},
    {"process_code": "GR-AX", "product_part": "AX-A", "name": "外圆磨削",
     "key_equipment": "GR-02"},
    {"process_code": "AS-GB", "product_part": "GB-G1", "name": "齿轮箱装配",
     "key_equipment": "AS-01"},
]

EQUIPMENT = [
    {"equipment_code": "HT-03", "name": "3 号热处理炉", "type": "热处理炉",
     "calibration_due": "2025-05-10"},
    {"equipment_code": "HT-02", "name": "2 号热处理炉", "type": "热处理炉",
     "calibration_due": "2025-08-01"},
    {"equipment_code": "MC-07", "name": "7 号数控车床", "type": "机加工设备",
     "calibration_due": "2025-12-01"},
    {"equipment_code": "GR-02", "name": "2 号外圆磨床", "type": "机加工设备",
     "calibration_due": "2025-11-01"},
    {"equipment_code": "AS-01", "name": "1 号装配线", "type": "装配线",
     "calibration_due": ""},
    {"equipment_code": "TF-02", "name": "便携式温度校验仪", "type": "校验仪器",
     "calibration_due": "2025-06-01"},
]

MEASUREMENT_ITEMS = [
    {"item_code": "HARD-HRC", "name": "表面硬度", "unit": "HRC",
     "spec_low": 48, "spec_high": 56, "related_defects": "DEF-HARD-LOW"},
    {"item_code": "STRAIGHT-MM", "name": "直线度", "unit": "mm",
     "spec_low": 0.0, "spec_high": 0.02, "related_defects": "DEF-STRAIGHT"},
    {"item_code": "RA-UM", "name": "表面粗糙度 Ra", "unit": "um",
     "spec_low": 0.0, "spec_high": 0.8, "related_defects": ""},
    {"item_code": "NOISE-DB", "name": "运转噪声", "unit": "dB(A)",
     "spec_low": 0.0, "spec_high": 72.0, "related_defects": "DEF-NOISE"},
]

DEFECT_CODES = [
    {"defect_code": "DEF-HARD-LOW", "name": "表面硬度偏低", "severity": "major",
     "default_disposition": "返工"},
    {"defect_code": "DEF-STRAIGHT", "name": "直线度超差", "severity": "major",
     "default_disposition": "返工"},
    {"defect_code": "DEF-SCRATCH", "name": "表面划伤", "severity": "minor",
     "default_disposition": "让步接收评审"},
    {"defect_code": "DEF-NOISE", "name": "运转异响", "severity": "critical",
     "default_disposition": "退回总装"},
]

PERSONNEL = [
    {"employee_id": "E0001", "name": "王质量", "role": "质量工程师", "group": "质量部"},
    {"employee_id": "E0002", "name": "李工艺", "role": "工艺工程师", "group": "工艺部"},
    {"employee_id": "E0003", "name": "赵班长", "role": "热处理班长", "group": "热处理车间"},
    {"employee_id": "E0004", "name": "陈质量经理", "role": "质量经理", "group": "质量部"},
]


def _master_rows() -> Dict[str, List[dict]]:
    return {
        "products.csv": PRODUCTS,
        "processes.csv": PROCESSES,
        "equipment.csv": EQUIPMENT,
        "measurement_items.csv": MEASUREMENT_ITEMS,
        "defect_codes.csv": DEFECT_CODES,
        "personnel.csv": PERSONNEL,
    }


# ---------------------------------------------------------------------------
# 输出工具
# ---------------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"cannot write empty csv: {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write(content)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class Generated:
    """记录已生成文件，便于最后统一生成资产台账与 manifest。"""

    root: Path
    files: Dict[str, dict] = field(default_factory=dict)

    def add(self, rel_path: str, modality: str, doc_type: str,
            business_tags: List[str], entities: List[str]) -> None:
        self.files[rel_path] = {
            "source_file": rel_path,
            "modality": modality,
            "doc_type": doc_type,
            "business_tags": business_tags,
            "entities": entities,
        }


# ---------------------------------------------------------------------------
# 主数据
# ---------------------------------------------------------------------------
def generate_master(root: Path) -> Generated:
    master_dir = root / "01_master_data"
    ensure_dir(master_dir)
    out = Generated(root=root)
    for filename, rows in _master_rows().items():
        path = master_dir / filename
        write_csv(path, rows)
        entities = [r.get("part_no") or r.get("equipment_code") or r.get("item_code")
                    or r.get("defect_code") or "" for r in rows][:5]
        out.add(str(path.relative_to(root)), "table", "master_data",
                ["主数据"], entities)
    return out


# ---------------------------------------------------------------------------
# 表格类：SPC / 检验记录 / 不良品 / 维保 / 客诉
# ---------------------------------------------------------------------------
def _normal_value(rng: random.Random, mean: float, sd: float) -> float:
    return round(max(0.0, rng.gauss(mean, sd)), 2)


def generate_spc(root: Path, rng: random.Random) -> List[dict]:
    """生成 2025-05 电机轴表面硬度的 SPC 台账，内嵌与数据规格一致的失控情节。"""
    records_dir = root / "03_quality_records"
    ensure_dir(records_dir)
    rows: List[dict] = []
    chart = "spc_hardness_HT03_202505.png"

    def push_sample(sample_no: str, batch_id: str, measured_at: str, value: float) -> None:
        rows.append({
            "sample_no": sample_no,
            "batch_id": batch_id,
            "part_no": "AX-A",
            "process_code": "HT-AX",
            "equipment_code": "HT-03",
            "item_code": "HARD-HRC",
            "measured_at": measured_at,
            "value": value,
            "spec_low": 48,
            "spec_high": 56,
            "result": "OK" if value >= 48 else "NG",
            "chart_ref": chart,
        })

    sample_idx = 0
    for batch_id, base_time, mean, sd in (
            ("AX-20250506-01", "2025-05-06 10:00", 51.8, 1.2),
            ("AX-20250508-01", "2025-05-08 10:00", 51.7, 1.1)):
        for i in range(5):
            sample_idx += 1
            push_sample(f"AX-S{sample_idx:04d}", batch_id, base_time,
                        _normal_value(rng, mean, sd))

    drift_means = [50.0, 49.0, 48.3]
    drift_batches = [
        ("AX-20250512-01", "2025-05-12 10:00"),
        ("AX-20250514-01", "2025-05-14 10:00"),
        ("AX-20250516-01", "2025-05-16 10:00"),
    ]
    for (batch_id, base_time), mean in zip(drift_batches, drift_means):
        for i in range(5):
            sample_idx += 1
            push_sample(f"AX-S{sample_idx:04d}", batch_id, base_time,
                        _normal_value(rng, mean, 0.8))

    rng_ng = random.Random(180518)
    failure_batch = "AX-20250518-01"
    for idx in range(42):
        sample_idx += 1
        push_sample(f"{failure_batch}-{idx + 1:03d}", failure_batch,
                    "2025-05-18 14:22", round(rng_ng.uniform(45.5, 47.4), 1))

    recover_batch = "AX-20250520-01"
    for i in range(5):
        sample_idx += 1
        push_sample(f"AX-S{sample_idx:04d}", recover_batch, "2025-05-20 16:00",
                    _normal_value(rng, 51.6, 1.1))

    path = records_dir / "spc_hardness_axis_202505.csv"
    write_csv(path, rows)
    return rows


def generate_other_records(root: Path) -> None:
    records_dir = root / "03_quality_records"
    ensure_dir(records_dir)

    write_csv(records_dir / "inspection_records_2025H1.csv", [
        {
            "record_id": "IR-20250518-01", "batch_id": "AX-20250518-01",
            "part_no": "AX-A", "item_code": "HARD-HRC", "inspected_at": "2025-05-18 15:00",
            "sample_size": 42, "ng_qty": 42, "result": "NG",
            "finding_ref": "WI-HT-AX/5.3",
        },
        {
            "record_id": "IR-20250522-01", "batch_id": "AX-20250518-01",
            "part_no": "AX-A", "item_code": "HARD-HRC", "inspected_at": "2025-05-22 10:00",
            "sample_size": 42, "ng_qty": 0, "result": "OK",
            "finding_ref": "QP-INC-03/4.3",
        },
    ])

    write_csv(records_dir / "nonconformity_records.csv", [
        {
            "nc_id": "NC-20250518-001", "batch_id": "AX-20250518-01", "qty": 42,
            "defect_code": "DEF-HARD-LOW", "found_process": "HT-AX",
            "finding_ref": "WI-HT-AX/5.3", "disposition": "返工",
            "disposition_reason": "硬度低于 48 HRC 下限，按 QP-INC-03 4.3 返工并复检",
            "status": "Reworked", "owner": "E0001",
        },
    ])

    write_csv(records_dir / "maintenance_logs.csv", [
        {
            "maintenance_id": "MT-20250511-01", "equipment_code": "HT-03",
            "equipment_name": "3 号热处理炉", "detected_at": "2025-05-11 08:30",
            "issue": "热电偶校准超期", "action": "安排校准",
            "status": "Open", "owner": "E0003", "closed_at": "",
        },
        {
            "maintenance_id": "MT-20250520-01", "equipment_code": "HT-03",
            "equipment_name": "3 号热处理炉", "detected_at": "2025-05-20 09:00",
            "issue": "更换热电偶并完成现场校准",
            "action": "更换备件并使用 TF-02 校验", "status": "Closed", "owner": "E0003",
            "closed_at": "2025-05-20 11:30",
        },
    ])

    write_csv(records_dir / "customer_complaints.csv", [
        {
            "complaint_id": "CP-20250610-01", "product_part": "GB-G1",
            "batch_id": "GB-20250608-01", "complained_at": "2025-06-10",
            "issue": "运转异响", "defect_code": "DEF-NOISE", "status": "UnderInvestigation",
            "note": "异响批次为装配线 AS-01 生产，与 AX 轴硬度批次不直接同批",
        },
    ])


# ---------------------------------------------------------------------------
# 文本类质量文档
# ---------------------------------------------------------------------------
QUALITY_DOCS: Dict[str, str] = {
    "QP-INC-03-不合格品控制程序.md": """# QP-INC-03 不合格品控制程序

> 衡星精工内部程序文件（合成演示版，非真实企业文件）。

## 1 目的

规范不合格品标识、隔离、评审与处置，防止误用放行。

## 2 适用范围

适用于原材料、在制品、成品检验中发现的不合格品。

## 3 判定

- 3.1 检验依据对应产品检验规范（如 SP-INSP-AX）；
- 3.2 实测值超出规格上下限即判定 NG；
- 3.3 NG 批次应隔离标识并开立不合格品单。

## 4 处置路径

- 4.1 **返工**：按作业指导书返工后必须重新检验，合格方可转序；
- 4.2 **报废**：无法返工或返工不经济时执行报废；
- 4.3 **让步接收**：仅当客户书面同意且经质量经理批准时允许；让步应记录范围与理由；
- 4.4 返工批次保留原始记录与复检记录，全程可追溯。

## 5 记录

不合格品单（NC）、复检记录（IR）应保存不少于 3 年。
""",
    "WI-HT-AX-热处理作业指导书.md": """# WI-HT-AX 电机轴淬火回火作业指导书

## 1 设备

3 号热处理炉（HT-03）或经评估等效的 2 号热处理炉（HT-02）。

## 2 关键参数（摘要）

- 淬火加热温度约 820–860 °C，油淬；
- 回火温度约 180–220 °C；
- 每批首件与末件进行表面硬度抽检（HARD-HRC 48–56）。

## 3 过程控制

- 3.1 设备热电偶应处于校准有效期内；
- 3.2 发现校准超期或温度异常应立即停止生产并通知设备/质量人员；
- 3.3 每批填写 SPC 记录并纳入控制图监控。

## 4 异常处理

出现硬度偏低或连续漂移时，按 QP-INC-03 处置并追溯同设备相关批次。
""",
    "WI-MC-AX-精加工作业指导书.md": """# WI-MC-AX 电机轴数控精车作业指导书

## 1 设备

7 号数控车床（MC-07）。

## 2 关键控制

- 装夹基准与图纸一致；
- 首件检验尺寸、直线度（STRAIGHT-MM ≤ 0.02 mm）；
- 加工完成后清洁去毛刺，按批次流转。

## 3 记录

工序流转卡随批次保存，可追溯设备、人员与时间。
""",
    "SP-INSP-AX-电机轴检验规范.md": """# SP-INSP-AX 电机轴检验规范

## 1 检验项目与判据

| 项目 | 代码 | 规格 | 抽样 |
|---|---|---|---|
| 表面硬度 | HARD-HRC | 48–56 HRC | 每批 5 件，首末件必检 |
| 直线度 | STRAIGHT-MM | ≤ 0.02 mm | 每批 5 件 |
| 表面粗糙度 | RA-UM | Ra ≤ 0.8 um | 每批 3 件 |

## 2 判定

任一样本超出规格即判该批对应项目 NG；NG 后执行加严抽样并按 QP-INC-03 处置。

## 3 引用

- QP-INC-03 不合格品控制程序
- WI-HT-AX 热处理作业指导书
""",
    "STD-GB-T19001-摘要.md": """# 标准要点摘要（非原文）

> 本文件为衡星精工质量手册引用的标准要点**自编摘要**，仅保留概念锚点，不作为标准原文使用。

## 8.5 生产和服务提供的控制（概念对应）

- 应有受控条件，包括作业指导、适宜设备、监视测量资源；
- 出现不符合时应停止并按控制程序处置。

## 8.6 产品和服务的放行（概念对应）

- 放行应基于完成规定的验证/检验，并保留形成文件的信息。

## 8.7 不合格输出的控制（概念对应）

- 应标识、隔离并评审不符合，防止误用；
- 处置方式包括纠正（返工）、报废或经授权让步；
- 让步应取得顾客许可（如适用）并保留记录。

内部锚点：STD:GB/T19001:8.5 / 8.6 / 8.7
""",
}


def generate_docs(root: Path) -> None:
    docs_dir = root / "02_quality_docs"
    ensure_dir(docs_dir)
    for filename, content in QUALITY_DOCS.items():
        write_text(docs_dir / filename, content)


# ---------------------------------------------------------------------------
# 可视化证据（可选 matplotlib）
# ---------------------------------------------------------------------------
def generate_images(root: Path) -> bool:
    """matplotlib 可用时生成控制图与温度示意；否则返回 False。"""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    img_dir = root / "04_visual_evidence"
    ensure_dir(img_dir)

    xs = list(range(1, 18))
    ys = [51.9, 51.5, 52.1, 51.7, 52.3, 50.1, 49.8, 49.4, 48.7,
          48.4, 48.1, 47.2, 46.8, 46.5, 46.1, 47.0, 51.7]
    fig, ax = plt.subplots(figsize=(7, 4), dpi=110)
    ax.plot(xs, ys, marker="o", color="#1f77b4", label="Xbar")
    ax.axhline(48.0, color="#d62728", linestyle="--", label="规格下限 48")
    ax.axhline(51.8, color="#2ca02c", linestyle=":", label="CL")
    ax.set_title("SPC - 表面硬度 HT-03 (2025-05 示意)")
    ax.set_xlabel("子组序号")
    ax.set_ylabel("HRC")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(img_dir / "spc_hardness_HT03_202505.png")
    plt.close(fig)

    tx = list(range(1, 19))
    ty = [838, 841, 835, 839, 836, 834, 831, 828, 825, 822, 820,
          817, 814, 810, 806, 803, 838, 841]
    fig2, ax2 = plt.subplots(figsize=(7, 3.6), dpi=110)
    ax2.plot(tx, ty, marker="s", color="#ff7f0e", label="炉温")
    ax2.axhline(820, color="#d62728", linestyle="--", label="工艺下限 820")
    ax2.set_title("3 号热处理炉炉温趋势 (2025-05 示意)")
    ax2.set_xlabel("日期序号")
    ax2.set_ylabel("°C")
    ax2.legend(fontsize=8)
    fig2.tight_layout()
    fig2.savefig(img_dir / "oven_temperature_HT03_202505.png")
    plt.close(fig2)

    import numpy as np

    grid_x, grid_y = np.meshgrid(np.linspace(0, 1, 220), np.linspace(0, 1, 110))
    z = 52 - 4.5 * np.exp(-((grid_x - 0.48) ** 2 + (grid_y - 0.52) ** 2) * 28)
    fig3, ax3 = plt.subplots(figsize=(5.5, 3.2), dpi=110)
    im = ax3.imshow(z, cmap="viridis", vmin=44, vmax=54)
    ax3.set_title("硬度剖面示意（加热不均演示）")
    fig3.colorbar(im, ax=ax3, label="HRC")
    fig3.tight_layout()
    fig3.savefig(img_dir / "hardness_profile_schematic.png")
    plt.close(fig3)
    return True


# ---------------------------------------------------------------------------
# 汇总产物：manifest 与资产台账
# ---------------------------------------------------------------------------
def summarize(root: Path, out: Generated, rng_seed: int) -> None:
    img_dir = root / "04_visual_evidence"
    if img_dir.exists():
        for img in sorted(img_dir.glob("*.png")):
            out.add(str(img.relative_to(root)), "image", "visual_evidence",
                    ["控制图", "质量证据"], ["HT-03", "HARD-HRC"])

    ledger_rows: List[dict] = []
    asset_seq = 0
    for rel_path in sorted(out.files):
        info = out.files[rel_path]
        asset_seq += 1
        full_path = root / rel_path
        ledger_rows.append({
            "asset_id": f"AST-20260903-{asset_seq:04d}",
            "source_file": rel_path,
            "modality": info["modality"],
            "doc_type": info["doc_type"],
            "business_tags": ";".join(info["business_tags"]),
            "entities": ";".join(e for e in info["entities"] if e),
            "checksum": sha256_of(full_path),
            "chunk_ids": "",
            "ingested_at": INGESTED_AT,
        })
    write_csv(root / "assets_ledger.csv", ledger_rows)

    write_json(root / "manifest.json", {
        "generator_version": GENERATOR_VERSION,
        "seed": rng_seed,
        "file_count": len(out.files),
        "asset_ledger_count": len(ledger_rows),
        "visual_evidence_generated": (img_dir / "spc_hardness_HT03_202505.png").exists(),
        "files": sorted(out.files),
    })


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data/generated",
                        help="输出根目录（默认 data/generated）")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="随机种子（默认 20250903）")
    parser.add_argument("--skip-images", action="store_true",
                        help="跳过 matplotlib 图片生成")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅打印计划产物，不写盘")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.output_dir)
    rng = random.Random(args.seed)

    if args.dry_run:
        print(f"[dry-run] generator={GENERATOR_VERSION} seed={args.seed} output={root}")
        print("[dry-run] 01_master_data: 6 csv")
        print("[dry-run] 02_quality_docs: 5 markdown")
        print("[dry-run] 03_quality_records: 5 csv")
        print("[dry-run] 04_visual_evidence: 3 png (matplotlib 可用时)")
        print("[dry-run] assets_ledger.csv + manifest.json")
        return 0

    ensure_dir(root)
    master_out = generate_master(root)
    spc_rows = generate_spc(root, rng)
    generate_other_records(root)
    generate_docs(root)
    images_ok = not args.skip_images and generate_images(root)

    merged = Generated(root=root)
    merged.files.update(master_out.files)
    for filename in QUALITY_DOCS:
        rel = f"02_quality_docs/{filename}"
        merged.add(rel, "text", "quality_doc", ["质量文件"],
                   ["AX-A", "HARD-HRC", "QP-INC-03"])
    for rel in (
        "03_quality_records/spc_hardness_axis_202505.csv",
        "03_quality_records/inspection_records_2025H1.csv",
        "03_quality_records/nonconformity_records.csv",
        "03_quality_records/maintenance_logs.csv",
        "03_quality_records/customer_complaints.csv",
    ):
        tags = ["2025-05", "AX-A", "HT-03"] if "spc" in rel else ["质量台账"]
        merged.add(rel, "table", "quality_record", tags,
                   ["AX-20250518-01", "HT-03", "HARD-HRC"])

    summarize(root, merged, args.seed)

    n_csv = len(list(root.rglob("*.csv")))
    n_md = len(list(root.rglob("*.md")))
    n_png = len(list(root.rglob("*.png")))
    print(f"生成完成: csv={n_csv} md={n_md} png={n_png} "
          f"spc_rows={len(spc_rows)} images={images_ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
