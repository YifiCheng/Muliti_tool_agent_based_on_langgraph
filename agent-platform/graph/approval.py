from typing import Literal

from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    approval_type: Literal["sql_query"] = "sql_query"
    thread_id: str
    session_id: str
    trace_id: str
    tool_name: str
    query: str
    reason: str
    risk: Literal["low", "medium", "high"] = "medium"


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = ""


def requires_approval(
    selected_tools: list[str],
    *,
    require_sql_approval: bool,
) -> bool:
    return require_sql_approval and "sql_query" in selected_tools