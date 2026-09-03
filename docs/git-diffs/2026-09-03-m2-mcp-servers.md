# Git Diff 总结：M2 T2.3 MCP Server 骨架

- 日期：2026-09-03
- 里程碑：M2 平台与基础集成，子任务 T2.3（MCP 服务脚手架）

## 涉及文件

### 新增

- `mcp_servers/README.md`：三个服务的职责、目录约定与 Nexent 接入方式
- `mcp_servers/__init__.py`、`mcp_servers/common.py`：包初始化与共享工具（CSV/JSONL/SHA-256/路径）
- `mcp_servers/asset_cognition_server/`：资产卡片核心逻辑 + FastMCP 包装
  - `asset_cognition_core.py`：卡片生成/校验、台账读取、实体检索、登记
  - `server.py`：`validate_asset_card`、`register_asset_tool`、`find_assets_by_entity_tool`
- `mcp_servers/kg_ontology_server/`：本体/图谱核心逻辑 + FastMCP 包装
  - `kg_ontology_core.py`：SQLite GraphStore、三元组 upsert、邻域检索、版本 diff（支持内存库测试）
  - `server.py`：`graph_search`、`add_triple`、`ontology_diff`
- `mcp_servers/decision_trace_server/`：决策证据链核心逻辑 + FastMCP 包装
  - `decision_trace_core.py`：EvidenceChain、断言覆盖检查、Markdown/Mermaid 渲染
  - `server.py`：`build_trace`、`check_trace`、`render_trace`
- `tests/test_mcp_cores.py`：三个服务核心逻辑测试（不依赖 mcp 包、不写盘）

### 修改

- `README.md`：目录树与里程碑状态同步（MCP 代码层完成，平台联调待环境）

## 变更要点

1. 采用“纯逻辑 core + FastMCP 包装”分层：核心模块只用标准库，可在无 mcp 依赖、无 Nexent 环境下单测；
   接入平台时安装 `mcp` 后运行 `server.py` 即可暴露工具。
2. 资产认知服务补齐“资产卡片注册/校验/检索”，可作为生成器资产台账的在线补充层。
3. 图谱服务提供 SQLite 降级实现，支持评审环境轻量运行；后续可替换为 Neo4j 适配器，接口保持稳定。
4. 决策证据链服务让“每条断言都有证据、结论可溯源”成为可校验、可渲染的工程对象。

## 测试与验收

- 21 项 `unittest` 全部通过（新增 8 项 MCP 核心测试）。
- 18 个 Python 文件只读语法编译检查通过。
- 平台联调（注册到 Nexent、工具测试面板验证）依赖 Nexent 部署，未在本机执行。

## 注意事项 / 影响

- `server.py` 需要 `mcp>=1.0`（见 `requirements.txt`），本阶段未安装以保持纯逻辑测试独立。
- MCP 工具默认台账/图谱路径为 `data/generated/` 与 `data/graph_store.sqlite`，接入时可通过工具参数覆盖。
