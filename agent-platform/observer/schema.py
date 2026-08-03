from typing import Any, Literal

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    trace_id: str
    session_id: str
    event_type: Literal["node", "tool", "llm", "error"]
    name: str
    status: Literal["success", "failed"] = "success"
    input_summary: str = ""
    output_summary: str = ""
    latency_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None