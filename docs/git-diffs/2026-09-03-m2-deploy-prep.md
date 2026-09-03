# Git Diff 总结：M2 T2.1 部署准备（文档/模板/就绪检查）

- 日期：2026-09-03
- 里程碑：M2 平台与基础集成，子任务 T2.1

## 涉及文件

### 新增

- `deploy/README.md`：Nexent Docker 部署步骤、硬件建议、模型接入建议、安全要点
- `deploy/nexent-deploy-checklist.md`：部署前/初始化/功能验收清单及当前环境状态
- `deploy/env.example`：模型/镜像源/端口参考环境变量模板（不含真实 Key）
- `scripts/check_nexent_env.py`：只读环境就绪检查（Python/Git/Docker/Compose/磁盘）

### 修改

- `README.md`：T2.1 状态细化（准备完成、实例启动阻塞）

## 变更要点

1. 明确 Nexent 官方安装入口与推荐 Docker 部署流程，避免把离线开发与平台部署混为一谈。
2. 模型接入按 LLM / VLM / Embedding（含多模态）分类给出供应商建议，与后续知识库绑定策略一致。
3. 就绪检查器可复用于任何目标机器；当前环境输出：Python/Git/磁盘通过，Docker 缺失。

## 测试与验收

- `python scripts/check_nexent_env.py` 运行正常，正确报告 Docker 缺失（exit=2）。
- 平台启动、模型连通与知识库创建仍需 Docker 与 API Key，标记为环境阻塞。

## 注意事项 / 影响

- `.env` 仅存本地，禁止提交；`deploy/env.example` 只作占位模板。
- 后续在具备 Docker 的机器部署后，应按 checklist 的 C 段完成功能验收再继续 M2/T2.2 检索指标。
