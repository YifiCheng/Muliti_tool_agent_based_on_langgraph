from typing import Any

from reflection.models import ReflectionDecision


class RuleReflector:
    """Detect obvious missing or unusable tool results before calling the LLM."""

    def reflect(
        self,
        *,
        query: str,
        tool_results: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> ReflectionDecision:
        if not tool_results:
            return ReflectionDecision(
                is_sufficient=False,
                missing_info=["no tool result"],
                next_action="retrieve_more",
                replan_query=query,
                reason="No tool result was returned.",
                source="rule",
            )

        failed_results = [
            result for result in tool_results if not result.get("success", False)
        ]
        if len(failed_results) == len(tool_results):
            return ReflectionDecision(
                is_sufficient=False,
                missing_info=["all selected tools failed"],
                next_action="retrieve_more",
                replan_query=query,
                reason="All selected tools failed.",
                source="rule",
            )

        document_results = [
            result
            for result in tool_results
            if result.get("tool_name")
            in {"document_search", "mock_document_search"}
        ]
        if document_results and not evidence:
            return ReflectionDecision(
                is_sufficient=False,
                missing_info=["document evidence"],
                next_action="retrieve_more",
                replan_query=query,
                reason="Document search returned no evidence.",
                source="rule",
            )

        sql_results = [
            result
            for result in tool_results
            if result.get("tool_name") in {"sql_query", "mock_sql"}
        ]
        if sql_results:
            row_count = sum(
                int(result.get("metadata", {}).get("row_count", 0))
                for result in sql_results
                if result.get("success", False)
            )
            if row_count == 0:
                return ReflectionDecision(
                    is_sufficient=False,
                    missing_info=["SQL query rows"],
                    next_action="retrieve_more",
                    replan_query=query,
                    reason="SQL query returned no rows.",
                    source="rule",
                )

        return ReflectionDecision(
            is_sufficient=True,
            missing_info=[],
            next_action="answer",
            reason="Tool results passed deterministic checks.",
            source="rule",
        )