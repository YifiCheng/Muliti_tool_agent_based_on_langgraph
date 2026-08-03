# 建议先用 `TypedDict`，便于后续 LangGraph 使用：


from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    user_query: str
    messages: list[dict[str, str]]
    plan: dict[str, Any]
    selected_tools: list[str]
    tool_results: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    reflection: dict[str, Any]
    final_answer: str
    iteration: int
    errors: list[str]