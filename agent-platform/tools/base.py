from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str
    content: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolRequest(BaseModel):
    query: str
    session_id: str
    trace_id: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    content: str = ""
    evidence: list[Evidence] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, request: ToolRequest) -> ToolResult:
        raise NotImplementedError