from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReflectionDecision(BaseModel):
    is_sufficient: bool
    missing_info: list[str] = Field(default_factory=list)
    next_action: Literal["answer", "retrieve_more"] = "answer"
    replan_query: str | None = None
    reason: str = ""
    source: Literal["rule", "llm", "fallback"] = "rule"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_action(self) -> "ReflectionDecision":
        if self.is_sufficient and self.next_action != "answer":
            raise ValueError(
                "A sufficient reflection must use next_action='answer'"
            )

        if not self.is_sufficient and self.next_action == "answer":
            raise ValueError(
                "An insufficient reflection cannot use next_action='answer'"
            )

        if self.next_action == "retrieve_more" and not self.missing_info:
            raise ValueError(
                "retrieve_more requires at least one missing_info item"
            )

        return self