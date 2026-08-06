from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    query: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    thread_id: str | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=10)
    require_sql_approval: bool = False


class AgentResumeRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    decision: Literal["approve", "reject"]
    reason: str = ""


class AgentRunResponse(BaseModel):
    status: Literal["completed", "interrupted"]
    session_id: str
    trace_id: str
    thread_id: str
    final_answer: str | None = None
    selected_tools: list[str] = Field(default_factory=list)
    approval_status: str | None = None
    interrupt: list[dict[str, Any]] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)


class AgentStateResponse(BaseModel):
    thread_id: str
    exists: bool
    state: dict[str, Any] = Field(default_factory=dict)


class TraceListResponse(BaseModel):
    trace_id: str
    events: list[dict[str, Any]] = Field(default_factory=list)