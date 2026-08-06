from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    trace_id: str
    user_query: str
    active_query: str
    replan_query: str | None
    messages: list[dict[str, str]]
    plan: dict[str, Any]
    selected_tools: list[str]
    current_tool_results: list[dict[str, Any]]
    current_evidence: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    reflection: dict[str, Any]
    final_answer: str
    iteration: int
    max_iterations: int
    errors: list[dict[str, Any]]
    thread_id: str
    approval_status: str
    approval_decision: dict[str, Any] | None