# Git Diff 总结：Nexent 本地部署成功（v2.4.1）

- 日期：2026-09-04
- 里程碑：M2 T2.1（本地部署落地）

## 变更要点

1. 系统侧：启用 WSL2/VirtualMachinePlatform（经两次重启完成），安装 Docker Desktop（wsl-2 后端）。
2. 镜像源：Docker Hub/GitHub 直连不可达；基础设施与核心镜像改用大陆镜像源
   `ccr.ccs.tencentyun.com/nexent-hub`。v2.5.1 的 web/data-process 标签在该源缺失，
   切换到官方 v2.4.1 标签完成部署。
3. 部署结果：基础设施（Elasticsearch/PostgreSQL/Redis/MinIO/Supabase）与核心服务
   （config/runtime/mcp/northbound/web/data-process）全部运行；
   http://localhost:3000 返回 200。
4. 默认超级管理员由部署脚本创建：`suadmin@nexent.com` / `Nexent@123`。

## 涉及文件

- `README.md`：T2.1 状态更新为“实例已启动”，模型接入仍待 Key
- `deploy/nexent-deploy-checklist.md`：本机部署状态勾选与默认管理员说明

## 注意事项 / 影响

- 后续 T2.2 知识库导入、T2.3 MCP 注册与 Skill 联调可直接在 localhost:3000 执行。
- 平台仍缺模型 API Key，模型配置完成后才能进行问答/检索验收。
- 部署源位于 `D:\nexent`（v2.4.1 detached HEAD），数据目录 `C:\Users\Administrator\nexent-data`。
