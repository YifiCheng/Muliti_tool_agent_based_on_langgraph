from typing import Any

from langgraph.types import Command

from api.schemas import (
    AgentResumeRequest,
    AgentRunRequest,
    AgentRunResponse,
    AgentStateResponse,
)
from config.settings import Settings, load_settings
from graph.app import build_agent_graph
from graph.checkpointer import build_sqlite_checkpointer
from graph.state import AgentState
from observer.sqlite_store import SQLiteTraceStore


class AgentService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.checkpointer = build_sqlite_checkpointer(self.settings)
        self.trace_store = SQLiteTraceStore(self.settings.observer.sqlite_path)
        self.graphs = {
            require_approval: build_agent_graph(
                settings=self.settings,
                trace_store=self.trace_store,
                checkpointer=self.checkpointer,
                require_sql_approval=require_approval,
            )
            for require_approval in (False, True)
        }

    def run(self, request: AgentRunRequest) -> AgentRunResponse:
        thread_id = request.thread_id or request.session_id
        graph = self.graphs[request.require_sql_approval]

        state: AgentState = {
            "session_id": request.session_id,
            "trace_id": request.trace_id,
            "thread_id": thread_id,
            "user_query": request.query,
            "messages": [{"role": "user", "content": request.query}],
            "iteration": 0,
            "max_iterations": request.max_iterations
            or self.settings.agent.max_iterations,
            "errors": [],
            "active_query": request.query,
            "replan_query": None,
            "approval_status": "not_required",
            "approval_decision": None,
            "current_tool_results": [],
            "current_evidence": [],
            "tool_results": [],
            "evidence": [],
        }
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(state, config=config)
        return self._to_run_response(
            result,
            session_id=request.session_id,
            trace_id=request.trace_id,
            thread_id=thread_id,
        )

    def resume(self, request: AgentResumeRequest) -> AgentRunResponse:
        config = {"configurable": {"thread_id": request.thread_id}}
        result = self.graphs[True].invoke(
            Command(
                resume={
                    "decision": request.decision,
                    "reason": request.reason,
                }
            ),
            config=config,
        )
        return self._to_run_response(
            result,
            session_id=result.get("session_id", ""),
            trace_id=result.get("trace_id", ""),
            thread_id=request.thread_id,
        )

    def get_state(self, thread_id: str) -> AgentStateResponse:
        snapshot = self.graphs[False].get_state(
            {"configurable": {"thread_id": thread_id}}
        )
        values = dict(snapshot.values or {})
        return AgentStateResponse(
            thread_id=thread_id,
            exists=bool(values),
            state=values,
        )

    def _to_run_response(
        self,
        result: dict[str, Any],
        *,
        session_id: str,
        trace_id: str,
        thread_id: str,
    ) -> AgentRunResponse:
        interrupts = _serialize_interrupts(result.get("__interrupt__", []))
        status = "interrupted" if interrupts else "completed"
        return AgentRunResponse(
            status=status,
            session_id=session_id,
            trace_id=trace_id,
            thread_id=thread_id,
            final_answer=result.get("final_answer"),
            selected_tools=result.get("selected_tools", []),
            approval_status=result.get("approval_status"),
            interrupt=interrupts,
            state={k: v for k, v in result.items() if k != "__interrupt__"},
        )


def _serialize_interrupts(interrupts: Any) -> list[dict[str, Any]]:
    if not interrupts:
        return []

    serialized = []
    for item in interrupts:
        serialized.append(
            {
                "id": getattr(item, "id", None),
                "value": getattr(item, "value", item),
            }
        )
    return serialized
