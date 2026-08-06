from typing import Any

from llm.client import LLMClient
from reflection.models import ReflectionDecision
from reflection.rule_reflector import RuleReflector


class LLMReflector:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def reflect(
        self,
        *,
        query: str,
        tool_results: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> ReflectionDecision:
        raw = self.llm.chat_json(
            [
                {
                    "role": "user",
                    "content": (
                        "请判断工具结果是否足以回答用户问题，只返回 JSON。\n"
                        f"用户问题: {query}\n"
                        f"工具结果: {tool_results}\n"
                        f"证据: {evidence}"
                    ),
                }
            ],
            schema_name="reflection",
        )
        decision = ReflectionDecision.model_validate(raw)
        return decision.model_copy(update={"source": "llm"})


class HybridReflector:
    """Run deterministic checks first, then ask the LLM when appropriate."""

    def __init__(
        self,
        llm: LLMClient,
        rule_reflector: RuleReflector | None = None,
    ) -> None:
        self.llm_reflector = LLMReflector(llm)
        self.rule_reflector = rule_reflector or RuleReflector()

    def reflect(
        self,
        *,
        query: str,
        tool_results: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> ReflectionDecision:
        rule_decision = self.rule_reflector.reflect(
            query=query,
            tool_results=tool_results,
            evidence=evidence,
        )
        if not rule_decision.is_sufficient:
            return rule_decision

        try:
            return self.llm_reflector.reflect(
                query=query,
                tool_results=tool_results,
                evidence=evidence,
            )
        except Exception as exc:
            return rule_decision.model_copy(
                update={
                    "source": "fallback",
                    "reason": (
                        "Rule checks passed, but LLM reflection failed: "
                        f"{exc}"
                    ),
                }
            )