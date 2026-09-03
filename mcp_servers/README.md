# mcp_servers/ 自建 MCP 服务

三个服务用于补足 Nexent 原生能力之外的工程化能力：

| 服务 | 核心职责 | 主要工具 |
|---|---|---|
| `asset_cognition_server` | 多模态资产的卡片化、注册、检索 | `register_asset`、`find_assets_by_entity`、`validate_asset_card` |
| `kg_ontology_server` | 本体/知识图谱读写、一致性、版本 diff | `graph_search`、`add_triple`、`consistency_check`、`ontology_diff` |
| `decision_trace_server` | 决策证据链构建与可视化 | `build_evidence_chain`、`check_assertion_coverage`、`render_trace` |

## 目录约定

```text
mcp_servers/
├─ <name>/
│  ├─ <name>_core.py   # 纯 Python 核心逻辑（标准库，可单测，不依赖 mcp 包）
│  └─ server.py        # FastMCP 包装：将核心函数暴露为标准工具
└─ README.md
```

## 运行

```powershell
pip install -r requirements.txt
python -m mcp_servers.asset_cognition_server.server
```

接入 Nexent 时使用官方“添加 MCP 服务（远程/容器化/OpenAPI 转 MCP）”入口，
将 server 启动地址或容器配置填入即可。工具可在 Nexent「测试工具」面板直接验证。

