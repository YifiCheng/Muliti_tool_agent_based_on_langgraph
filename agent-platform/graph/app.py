from typing import Any

from langgraph.graph import END, START, StateGraph

from config.settings import Settings, load_settings
from graph.checkpointer import build_sqlite_checkpointer
from graph.nodes import (
    build_approval_node,
    build_answer_node,
    build_plan_node,
    build_reflect_node,
    build_tool_node,
)
from graph.router import route_after_approval, route_after_reflect
from graph.state import AgentState
from llm.client import LLMClient, build_llm_client
from observer.sqlite_store import SQLiteTraceStore
from observer.trace_store import TraceStore
from tools.registry import ToolRegistry
from tools.registry_factory import build_agent_registry


def build_agent_graph(
    *,
    settings: Settings | None = None,
    llm: LLMClient | None = None,
    registry: ToolRegistry | None = None,
    trace_store: TraceStore | None = None,
    checkpointer: Any | None = None,
    require_sql_approval: bool = False,
):
    settings = settings or load_settings()
    llm = llm or build_llm_client(settings)
    registry = registry or build_agent_registry(settings)
    trace_store = trace_store or SQLiteTraceStore(settings.observer.sqlite_path)

    builder = StateGraph(AgentState)
    builder.add_node("plan", build_plan_node(llm, registry, trace_store))
    builder.add_node("tool", build_tool_node(registry, trace_store))
    builder.add_node("reflect", build_reflect_node(llm, trace_store))
    builder.add_node("answer", build_answer_node(llm, trace_store))

    builder.add_node(
        "approval",
        build_approval_node(
            require_sql_approval=require_sql_approval,
            trace_store=trace_store,
        ),
    )

    builder.add_edge(START, "plan")
    builder.add_edge("plan", "approval")
    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "tool": "tool",
            "answer": "answer",
        },
    )
    builder.add_edge("tool", "reflect")
    builder.add_conditional_edges(
        "reflect",
        route_after_reflect,
        {
            "plan": "plan",
            "answer": "answer",
        },
    )
    builder.add_edge("answer", END)

    if checkpointer is None:
        return builder.compile()

    return builder.compile(checkpointer=checkpointer)


def run_agent(
    query: str,
    *,
    session_id: str = "demo-session",
    trace_id: str = "demo-trace",
    max_iterations: int | None = None,
) -> AgentState:
    settings = load_settings()
    graph = build_agent_graph(
        settings=settings,
        checkpointer=build_sqlite_checkpointer(settings),
        require_sql_approval=settings.agent.require_sql_approval,
    )
    initial_state: AgentState = {
        "session_id": session_id,
        "trace_id": trace_id,
        "thread_id": session_id,
        "user_query": query,
        "messages": [{"role": "user", "content": query}],
        "iteration": 0,
        "max_iterations": max_iterations or settings.agent.max_iterations,
        "errors": [],
        "active_query": query,
        "replan_query": None,
        "approval_status": "not_required",
        "approval_decision": None,
        "current_tool_results": [],
        "current_evidence": [],
        "tool_results": [],
        "evidence": [],
    }
    config = {"configurable": {"thread_id": session_id}}
    return graph.invoke(initial_state, config=config)
