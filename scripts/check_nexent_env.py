"""T2.1 环境就绪检查（只读，不修改系统）。

检查 Python / Git / Docker / Docker Compose / 磁盘空间等部署 Nexent 的前置条件。

用法:
    python scripts/check_nexent_env.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    required: bool = True

    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"


def run_version(cmd: list[str]) -> str | None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or proc.stderr).strip().splitlines()[0] if (proc.stdout or proc.stderr) else ""


def check_tool(name: str, version_args: list[str]) -> CheckResult:
    exe = shutil.which(name)
    if not exe:
        return CheckResult(name=name, ok=False, detail="未找到可执行文件", required=False)
    version = run_version(version_args)
    return CheckResult(
        name=name,
        ok=version is not None,
        detail=version or "命令执行失败",
        required=False,
    )


def disk_free_gb(path: Path) -> float:
    try:
        usage = shutil.disk_usage(path)
        return usage.free / (1024 ** 3)
    except OSError:
        return -1.0


def main() -> int:
    results: list[CheckResult] = [
        CheckResult("Python", sys.version_info >= (3, 10),
                    detail=sys.version.split()[0]),
        check_tool("git", ["git", "--version"]),
        check_tool("docker", ["docker", "--version"]),
        check_tool("docker-compose", ["docker-compose", "--version"]),
    ]

    root = Path(__file__).resolve().parents[1]
    free = disk_free_gb(root)
    results.append(CheckResult(
        "DiskFreeGB", free >= 40,
        detail=f"{free:.1f} GiB free（建议 >= 40 GiB）",
        required=False,
    ))

    print("Nexent 部署环境检查")
    print("=" * 60)
    for item in results:
        if item.name in {"docker", "docker-compose"} and not item.ok:
            item.detail += " —— Docker 缺失时无法本地启动 Nexent"
        print(f"[{item.status():4s}] {item.name:16s} {item.detail}")
    print("=" * 60)

    critical = [r for r in results if r.required and not r.ok]
    docker_ok = any(r.name == "docker" and r.ok for r in results)
    print("结论：", "前置基础通过。" if not critical else "存在基础项未通过。")
    if not docker_ok:
        print("提示：请先安装 Docker（Windows 需 WSL2/Linux 容器），再按 deploy/README.md 部署 Nexent。")
    return 0 if not critical and docker_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
