# Nexent 本地部署与接入说明（T2.1）

> 状态：**文档与准备脚本已完成；实际部署需具备 Docker 的机器并配置模型 API Key**。
> 本机（当前开发环境）未安装 Docker/WSL，因此 T2.1 的平台启动步骤标记为“环境阻塞”。

## 1. 为什么需要 Nexent

衡策 EvoNex 的检索-推理执行流、知识库溯源、Skill/MCP 集成与智能体版本管理均运行在 Nexent 上。
离线开发产物（数据、本体、MCP 核心、评测集）不依赖 Nexent；但“平台可运行”验收必须在 Nexent 实例中完成。

## 2. 官方资源

- Nexent 代码仓（GitHub）：https://github.com/ModelEngine-Group/nexent
- Nexent 代码仓（GitCode）：https://gitcode.com/ModelEngine/nexent
- 中文文档：https://modelengine-group.github.io/nexent/zh/user-guide/home-page.html
- 英文文档：https://modelengine-group.github.io/nexent/en/user-guide/home-page.html

## 3. 推荐部署方案

### Docker（个人/小团队，推荐）

```bash
git clone https://github.com/ModelEngine-Group/nexent.git
cd nexent
bash deploy.sh docker
```

- 交互式部署可按菜单选择组件；非交互可用 `--defaults`。
- 成功后访问：http://localhost:3000，按安装向导完成初始化。
- 组件默认包含 `application / data-process / supabase`；基础设施（Elasticsearch、PostgreSQL、Redis、MinIO）自动拉起。

### 硬件建议

| 项目 | 最低 | 推荐 |
|---|---|---|
| CPU | 4 核 | 8 核 |
| 内存 | 8 GiB | 16 GiB |
| 磁盘 | 40 GiB | 100 GiB |
| 软件 | Docker 24+ / Docker Compose v2+ | 同左 |

> 本项目的知识库与 MCP 服务较多，按 8 核/16GiB/100GiB 规划更稳妥。

## 4. 模型接入建议

Nexent 支持 OpenAI 兼容接口，推荐按可用性选择：

| 用途 | 建议供应商/模型 | 备注 |
|---|---|---|
| LLM（推理） | SiliconFlow / 阿里百炼 / DeepSeek / Qwen | OpenAI 兼容，国内可用 |
| VLM（图片/文档视觉） | 支持视觉的 OpenAI 兼容 VLM | 用于 analyze-image 与图文证据 |
| Embedding（文本） | Jina / BGE 系 | 与知识库绑定，创建 KB 后不可随意更换 |
| Embedding（多模态） | DashScope / Jina 多模态 embedding | 图片内容需向量化时选择 |
| 公网搜索 | EXA / Tavily / Linkup | 可选，赛题场景以私有 KB 为主 |

先配置 **模型 → 知识库 → 智能体** 三步完成平台初始化。

## 5. 安全与运行要点

- `.env` 不入库；使用 `deploy/env.example` 复制为本地 `.env` 后填写。
- 自建 MCP 服务运行在独立进程/容器，接入 Nexent 时按“远程/容器化 MCP”配置并做工具测试。
- 评审/演示前关闭非必要公网访问，保留局域网可访问即可。

## 6. 就绪检查

```powershell
python scripts\check_nexent_env.py
```

检查项：Python、Git、Docker、Docker Compose、磁盘空间、网络出口。全部通过后再执行部署。
