# Git Diff 总结：M2 本机 Nexent 自动部署自恢复脚本

- 日期：2026-09-03
- 里程碑：M2 T2.1（补充：重启自恢复部署）

## 涉及文件

### 新增

- `deploy/auto-deploy.ps1`：重启后一键自动部署（功能检查 → Docker Desktop(wsl-2) → Nexent clone → deploy.sh → 健康检查 → 状态文件）
- `deploy/register-auto-task.ps1`：注册一次性 ONLOGON 最高权限计划任务 `CodexNexentDeploy`
- `deploy/diagnose-features.ps1`：Windows 功能状态诊断（Docker/Nexent 前置）

### 修改

- `deploy/README.md`：补充自动部署脚本说明

## 变更要点

1. 本机 Windows 的 WSL/VirtualMachinePlatform 处于“已暂存待重启”状态；启用后必须重启才能安装
   WSL2 与 Linux 容器，因此需要“重启后自动继续”的机制。
2. 计划任务 `CodexNexentDeploy` 已注册（Status: Ready），登录后以最高权限执行自动部署，
   完成后自删任务，避免重复运行。
3. 部署全程输出至 `D:\nexent-deploy.log`，结果写入 `D:\nexent-deploy-status.json`。

## 注意事项 / 影响

- 自动部署脚本包含 Docker Desktop 官方安装器下载与静默安装参数 `--accept-license --backend=wsl-2`。
- 若重启后功能仍无法启用或 Docker 无法启动，脚本会将状态置为 failed 并保留日志供排查。
