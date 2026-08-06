from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PlanDecision(BaseModel):
    tools: list[str] = Field(default_factory=list)
    reason: str = ""

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, tools: list[str]) -> list[str]:
        cleaned = [tool.strip() for tool in tools if tool.strip()]
        if not cleaned:
            raise ValueError("Plan must select at least one tool")
        return list(dict.fromkeys(cleaned))


class AgentError(BaseModel):
    category: Literal[
        "planning",
        "tool_lookup",
        "tool_execution",
        "reflection",
        "answer",
        "configuration",
    ]
    source: str
    message: str
    iteration: int = 0
    retryable: bool = False