# Nexent 部署与接入检查清单（T2.1）

## A. 部署前

- [ ] 有 Docker 24+ 与 Docker Compose v2+ 的机器（Linux/Windows 需启用 WSL2 或 Linux 容器）
- [ ] 硬件满足：8 核 / 16 GiB / 100 GiB（最低 4 核 / 8 GiB / 40 GiB）
- [ ] `git clone https://github.com/ModelEngine-Group/nexent.git`
- [ ] 阅读官方 Docker/K8s 部署文档，选择 Docker 路径
- [ ] 准备 OpenAI 兼容 LLM/VLM API Key 与 Embedding API Key
- [ ] `deploy/env/.env` 已按官方模板填写（本仓只提供参考 `deploy/env.example`）
- [ ] 端口 3000 未被占用，防火墙放行

## B. 部署与初始化

- [ ] `bash deploy.sh docker` 成功完成
- [ ] http://localhost:3000 打开安装向导并完成管理员初始化
- [ ] 模型管理：LLM / VLM / Embedding 分别接入并连通测试
- [ ] 创建 3 个知识库：标准规程库 / 台账与记录库 / 图片证据库（见 T2.2 规划）
- [ ] 上传 `data/generated/` 语料，确认解析/入库状态为 Ready
- [ ] 配置知识库自摘要与用户组权限

## C. 功能验收

- [ ] 知识库问答可返回带引用来源的答案
- [ ] 图片/表格类文件可被解析并参与检索
- [ ] MCP 服务注册成功，工具测试返回预期 JSON
- [ ] Skill 可安装并绑定到智能体
- [ ] 发布主智能体并能在“开始问答”中运行

## D. 本机（当前环境）状态

- [x] Python 3.12.10 可用
- [x] 离线合成数据可生成
- [x] MCP 核心逻辑与单测通过
- [x] Docker 可用（Docker Desktop wsl-2，server 29.7.2）
- [x] Nexent 实例已启动（v2.4.1，大陆镜像源 ccr.ccs.tencentyun.com/nexent-hub）
- [x] Nexent Web：http://localhost:3000 返回 200
- [ ] 模型 API Key 已配置（阻塞：无 Key）

> 默认管理员：`suadmin@nexent.com` / `Nexent@123`（部署脚本自动创建，首次登录后请尽快修改）。
