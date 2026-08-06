from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    trace_id: str
    user_query: str
    messages: list[dict[str, str]]
    plan: dict[str, Any]
    replan_query: str | None
    selected_tools: list[str]
    tool_results: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    reflection: dict[str, Any]
    final_answer: str
    iteration: int
    max_iterations: int
    errors: list[str]