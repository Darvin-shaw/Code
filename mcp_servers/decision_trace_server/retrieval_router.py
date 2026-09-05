"""M4 T4.1 检索路由与查询分解（纯逻辑，可离线测试）。

“检索-推理”双驱动：先判断问题类型与检索源，再生成取证/推理/反证/输出步骤。
"""

from __future__ import annotations

import re
from typing import Dict, List


CATEGORY_KEYWORDS = {
    "multimodal": ["控制图", "曲线", "图片", "截图", "图表", "图谱"],
    "numeric": ["多少", "范围", "最小值", "最大值", "平均值", "统计", "数量", "计数"],
    "doc-lookup": ["哪个文件", "哪个条款", "出自哪个", "条款依据", "依据条款"],
    "disposition": ["能否", "是否可", "让步接收", "返工", "报废", "处置", "放行"],
    "root-cause": ["原因", "根因", "为什么", "是否与", "相关"],
}

KB_PRIORITY = {
    "standard": "标准规程库",
    "records": "台账与记录库",
    "visual": "图片证据库",
}


def route_question(question: str) -> Dict[str, object]:
    """判断问题类型并给出检索优先级、图谱/表格需求与候选工具。"""
    text = question.strip()
    for category in ("multimodal", "numeric", "doc-lookup", "disposition", "root-cause"):
        if any(keyword in text for keyword in CATEGORY_KEYWORDS[category]):
            return _build_route(category, question)
    return _build_route("root-cause", question)


def _build_route(category: str, question: str) -> Dict[str, object]:
    if category == "numeric":
        kb_priority = ["kb_records"]
        needs_graph = False
        tools = ["knowledge_base_search", "analyze-text-file"]
    elif category == "multimodal":
        kb_priority = ["kb_visual"]
        needs_graph = False
        tools = ["analyze-image", "analyze-text-file"]
    elif category == "disposition":
        kb_priority = ["kb_standard"]
        needs_graph = True
        tools = ["knowledge_base_search", "graph_search", "analyze-text-file"]
    else:
        kb_priority = ["kb_standard", "kb_records"]
        needs_graph = True
        tools = ["knowledge_base_search", "graph_search", "analyze-text-file"]
    return {
        "category": category,
        "question": question,
        "kb_priority": kb_priority,
        "needs_graph": needs_graph,
        "tools": tools,
    }


def decompose_question(question: str, max_parts: int = 5) -> List[str]:
    """按显式分隔符拆分子问题；无分隔符时保持单问题。"""
    raw = [part.strip() for part in re.split(r"[；;\n。]", question) if part.strip()]
    return raw[: max(1, max_parts)] if raw else [question]


def evidence_plan(question: str) -> Dict[str, object]:
    """返回双驱动执行计划：检索 → 推理 → 反证 → 校验 → 结论。"""
    route = route_question(question)
    steps = [
        {"action": "retrieve", "target": route["kb_priority"]},
        {"action": "reason", "detail": "基于证据形成候选结论"},
        {"action": "counter_evidence", "detail": "检索反证并检查覆盖"},
        {"action": "verify", "detail": "确认每条断言均有引用"},
        {"action": "answer", "detail": "输出证据链与引用"},
    ]
    return {"route": route, "steps": steps, "sub_questions": decompose_question(question)}
