from typing import Any

from llm.client import LLMClient
from observer.trace_store import TraceStore, trace_span
from tools.base import ToolRequest, ToolResult
from tools.registry import ToolRegistry
from tools.runner import run_tool_safely

from graph.state import AgentState

from reflection.llm_reflector import HybridReflector


def build_plan_node(llm: LLMClient, trace_store: TraceStore | None = None):
    def plan_node(state: AgentState) -> dict[str, Any]:
        trace_id = state["trace_id"]
        session_id = state["session_id"]
        query = state["user_query"]
        iteration = state.get("iteration", 0) + 1

        def run() -> dict[str, Any]:
            plan = llm.chat_json(
                [{"role": "user", "content": query}],
                schema_name="plan",
            )
            selected_tools = plan.get("tools", [])
            return {
                "plan": plan,
                "selected_tools": selected_tools,
                "iteration": iteration,
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
            return update

    return plan_node


def build_tool_node(registry: ToolRegistry, trace_store: TraceStore | None = None):
    def tool_node(state: AgentState) -> dict[str, Any]:
        trace_id = state["trace_id"]
        session_id = state["session_id"]
        query = state["user_query"]
        selected_tools = state.get("selected_tools", [])
        results: list[ToolResult] = []

        for tool_name in selected_tools:
            tool = registry.get(tool_name)
            result = run_tool_safely(
                tool,
                ToolRequest(
                    query=query,
                    session_id=session_id,
                    trace_id=trace_id,
                ),
                trace_store=trace_store,
            )
            results.append(result)

        evidence = []
        for result in results:
            evidence.extend([item.model_dump() for item in result.evidence])

        return {
            "tool_results": [result.model_dump() for result in results],
            "evidence": evidence,
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
            answer = llm.chat(
                [
                    {
                        "role": "user",
                        "content": (
                            "请基于工具结果回答用户问题。\n"
                            f"用户问题: {query}\n"
                            f"工具结果: {tool_results}\n"
                            f"证据: {evidence}"
                        ),
                    }
                ]
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