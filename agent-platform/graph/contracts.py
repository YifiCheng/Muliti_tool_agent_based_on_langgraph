from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PlanDecision(BaseModel):
    tools: list[str] = Field(default_factory=list)
    reason: str = ""

    @field_validator("tools", mode="before")
    @classmethod
    def normalize_tools(cls, tools: Any) -> list[str]:
        if not isinstance(tools, list):
            raise ValueError("Plan tools must be a list")

        normalized: list[str] = []
        for item in tools:
            if isinstance(item, str):
                name = item.strip()
            elif isinstance(item, dict):
                name = str(item.get("name", "")).strip()
            else:
                name = ""
            if name:
                normalized.append(name)

        cleaned = list(dict.fromkeys(normalized))
        if not cleaned:
            raise ValueError("Plan must select at least one tool")
        return cleaned


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