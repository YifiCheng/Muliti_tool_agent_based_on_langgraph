from langgraph.graph import END, START, StateGraph

from config.settings import Settings, load_settings
from graph.nodes import (
    build_answer_node,
    build_plan_node,
    build_reflect_node,
    build_tool_node,
)
from graph.router import route_after_reflect
from graph.state import AgentState
from llm.client import LLMClient, build_llm_client
from observer.sqlite_store import SQLiteTraceStore
from observer.trace_store import TraceStore
from tools.registry_factory import build_agent_registry
from tools.registry import ToolRegistry


def build_agent_graph(
    *,
    settings: Settings | None = None,
    llm: LLMClient | None = None,
    registry: ToolRegistry | None = None,
    trace_store: TraceStore | None = None,
):
    settings = settings or load_settings()
    llm = llm or build_llm_client(settings)
    registry = registry or build_agent_registry(settings)
    trace_store = trace_store or SQLiteTraceStore(settings.observer.sqlite_path)

    builder = StateGraph(AgentState)
    builder.add_node("plan", build_plan_node(llm, trace_store))
    builder.add_node("tool", build_tool_node(registry, trace_store))
    builder.add_node("reflect", build_reflect_node(llm, trace_store))
    builder.add_node("answer", build_answer_node(llm, trace_store))

    builder.add_edge(START, "plan")
    builder.add_edge("plan", "tool")
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

    return builder.compile()


def run_agent(
    query: str,
    *,
    session_id: str = "demo-session",
    trace_id: str = "demo-trace",
    max_iterations: int | None = None,
) -> AgentState:
    settings = load_settings()
    graph = build_agent_graph(settings=settings)
    initial_state: AgentState = {
        "session_id": session_id,
        "trace_id": trace_id,
        "user_query": query,
        "messages": [{"role": "user", "content": query}],
        "iteration": 0,
        "max_iterations": max_iterations or settings.agent.max_iterations,
        "errors": [],
    }
    return graph.invoke(initial_state)