from typing import Any

from llm.client import LLMClient
from observer.trace_store import TraceStore, trace_span
from tools.base import ToolRequest, ToolResult
from tools.registry import ToolRegistry
from tools.runner import run_tool_safely

from graph.state import AgentState

from reflection.llm_reflector import HybridReflector

from graph.contracts import AgentError, PlanDecision
from graph.prompts import build_answer_messages, build_plan_messages
from graph.state_utils import (
    append_tool_results,
    collect_tool_errors,
    get_active_query,
    merge_evidence,
)


def build_plan_node(
    llm: LLMClient,
    registry: ToolRegistry,
    trace_store: TraceStore | None = None,
):
    def plan_node(state: AgentState) -> dict[str, Any]:
        trace_id = state["trace_id"]
        session_id = state["session_id"]
        query = get_active_query(state)
        iteration = state.get("iteration", 0) + 1

        def run() -> dict[str, Any]:
            try:
                raw_plan = llm.chat_json(
                    build_plan_messages(query, registry.descriptions()),
                    schema_name="plan",
                )
                plan = PlanDecision.model_validate(raw_plan)
                return {
                    "plan": plan.model_dump(),
                    "selected_tools": plan.tools,
                    "active_query": query,
                    "iteration": iteration,
                }
            except Exception as exc:
                error = AgentError(
                    category="planning",
                    source="plan",
                    message=str(exc),
                    iteration=iteration,
                    retryable=True,
                )
                return {
                    "plan": {
                        "tools": [],
                        "reason": "Planning failed.",
                    },
                    "selected_tools": [],
                    "active_query": query,
                    "iteration": iteration,
                    "errors": [*state.get("errors", []), error.model_dump()],
                }

        if trace_store is None:
            return run()

        with trace_span(
            trace_store,
            trace_id=trace_id,
            session_id=session_id,
            event_type="node",
            name="plan",
            input_summary=query,
            metadata={"iteration": iteration},
        ) as span:
            update = run()
            span["output_summary"] = ",".join(update["selected_tools"])
            span["metadata"]["active_query"] = query
            span["metadata"]["error_count"] = len(update.get("errors", []))
            return update

    return plan_node


def build_tool_node(
    registry: ToolRegistry,
    trace_store: TraceStore | None = None,
):
    def tool_node(state: AgentState) -> dict[str, Any]:
        trace_id = state["trace_id"]
        session_id = state["session_id"]
        query = state.get("active_query") or get_active_query(state)
        iteration = state.get("iteration", 0)
        selected_tools = state.get("selected_tools", [])
        results: list[ToolResult] = []

        for tool_name in selected_tools:
            try:
                tool = registry.get(tool_name)
            except Exception as exc:
                results.append(
                    ToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=str(exc),
                        metadata={"error_category": "tool_lookup"},
                    )
                )
                continue

            result = run_tool_safely(
                tool,
                ToolRequest(
                    query=query,
                    session_id=session_id,
                    trace_id=trace_id,
                ),
                trace_store=trace_store,
            )
            if not result.success:
                result.metadata["error_category"] = "tool_execution"
            results.append(result)

        current_results = [result.model_dump() for result in results]
        current_evidence: list[dict[str, Any]] = []
        for result in results:
            current_evidence.extend(
                item.model_dump() for item in result.evidence
            )

        accumulated_results = append_tool_results(
            state.get("tool_results", []),
            current_results,
        )
        accumulated_evidence = merge_evidence(
            state.get("evidence", []),
            current_evidence,
        )
        new_errors = collect_tool_errors(
            current_results,
            iteration=iteration,
        )

        return {
            "current_tool_results": current_results,
            "current_evidence": current_evidence,
            "tool_results": accumulated_results,
            "evidence": accumulated_evidence,
            "errors": [*state.get("errors", []), *new_errors],
        }

    return tool_node


def build_reflect_node(
    llm: LLMClient,
    trace_store: TraceStore | None = None,
    reflector: HybridReflector | None = None,
):
    reflector = reflector or HybridReflector(llm)

    def reflect_node(state: AgentState) -> dict[str, Any]:
        trace_id = state["trace_id"]
        session_id = state["session_id"]
        query = state["user_query"]
        tool_results = state.get("tool_results", [])
        evidence = state.get("evidence", [])

        def run() -> dict[str, Any]:
            decision = reflector.reflect(
                query=query,
                tool_results=tool_results,
                evidence=evidence,
            )
            return {
                "reflection": decision.model_dump(),
                "replan_query": decision.replan_query,
            }

        if trace_store is None:
            return run()

        with trace_span(
            trace_store,
            trace_id=trace_id,
            session_id=session_id,
            event_type="node",
            name="reflect",
            input_summary=query,
        ) as span:
            update = run()
            reflection = update["reflection"]
            span["output_summary"] = reflection["next_action"]
            span["metadata"]["is_sufficient"] = reflection["is_sufficient"]
            span["metadata"]["source"] = reflection["source"]
            return update

    return reflect_node


def build_answer_node(llm: LLMClient, trace_store: TraceStore | None = None):
    def answer_node(state: AgentState) -> dict[str, Any]:
        trace_id = state["trace_id"]
        session_id = state["session_id"]
        query = state["user_query"]
        tool_results = state.get("tool_results", [])
        evidence = state.get("evidence", [])

        def run() -> dict[str, Any]:
            errors = state.get("errors", [])
            answer = llm.chat(
                build_answer_messages(
                    query=query,
                    tool_results=tool_results,
                    evidence=evidence,
                    errors=errors,
                )
            )
            return {"final_answer": answer}

        if trace_store is None:
            return run()

        with trace_span(
            trace_store,
            trace_id=trace_id,
            session_id=session_id,
            event_type="node",
            name="answer",
            input_summary=query,
        ) as span:
            update = run()
            span["output_summary"] = update["final_answer"][:200]
            return update

    return answer_node