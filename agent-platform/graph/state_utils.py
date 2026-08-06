from typing import Any

from graph.contracts import AgentError


def get_active_query(state: dict[str, Any]) -> str:
    replan_query = state.get("replan_query")
    if isinstance(replan_query, str) and replan_query.strip():
        return replan_query.strip()
    return str(state["user_query"])


def append_tool_results(
    existing: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [*existing, *current]


def merge_evidence(
    existing: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for item in [*existing, *current]:
        key = (
            str(item.get("source", "")),
            str(item.get("content", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    return merged


def collect_tool_errors(
    results: list[dict[str, Any]],
    *,
    iteration: int,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    for result in results:
        if result.get("success", False):
            continue

        metadata = result.get("metadata", {})
        category = metadata.get("error_category", "tool_execution")
        error = AgentError(
            category=category,
            source=str(result.get("tool_name", "unknown_tool")),
            message=str(result.get("error") or "Unknown tool error"),
            iteration=iteration,
            retryable=category != "tool_lookup",
        )
        errors.append(error.model_dump())

    return errors