from typing import Any, Literal

from pydantic import BaseModel, Field


class EvalDatasetMetadata(BaseModel):
    name: str = "default"
    description: str = ""
    rag_docs_dir: str | None = None


class EvalCase(BaseModel):
    case_id: str
    category: Literal["rag", "sql", "calculator", "approval", "fallback"] = "rag"
    query: str
    query_language: Literal["zh", "en"] = "zh"
    expected_tools: list[str] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)
    expected_sources: list[str] = Field(default_factory=list)
    require_evidence: bool = False
    min_evidence_count: int = Field(default=0, ge=0)
    require_approval: bool = False
    approval_decision: Literal["approve", "reject"] | None = None
    max_iterations: int = Field(default=3, ge=1, le=10)


class EvalCaseResult(BaseModel):
    case_id: str
    category: str
    query: str
    passed: bool
    score: float
    selected_tools: list[str] = Field(default_factory=list)
    final_answer: str = ""
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalReport(BaseModel):
    total: int
    passed: int
    pass_rate: float
    average_score: float
    by_category: dict[str, dict[str, Any]] = Field(default_factory=dict)
    results: list[EvalCaseResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)