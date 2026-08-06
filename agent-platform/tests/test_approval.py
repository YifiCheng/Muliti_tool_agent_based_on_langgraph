from graph.app import build_agent_graph
from graph.approval import ApprovalDecision, requires_approval
from graph.checkpointer import build_memory_checkpointer
from langgraph.types import Command
from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from observer.sqlite_store import SQLiteTraceStore
from tests.test_sql_tool import create_test_db
from tools.mock_tools import MockCalculatorTool
from tools.registry import ToolRegistry
from tools.sql_tool import SQLQueryTool, SQLiteExecutor


def test_sql_can_require_approval():
    assert requires_approval(
        ["sql_query"],
        require_sql_approval=True,
    )


def test_sql_does_not_require_approval_by_default():
    assert not requires_approval(
        ["sql_query"],
        require_sql_approval=False,
    )


def test_approval_decision_accepts_approve():
    decision = ApprovalDecision(
        decision="approve",
        reason="reviewed",
    )
    assert decision.decision == "approve"


def test_approval_decision_rejects_unknown_value():
    from pydantic import ValidationError

    try:
        ApprovalDecision(decision="maybe")
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid approval decision was accepted")


def test_rejected_sql_approval_does_not_execute_sql(tmp_path):
    registry = ToolRegistry()
    registry.register(
        SQLQueryTool(SQLiteExecutor(create_test_db(tmp_path)))
    )
    registry.register(MockCalculatorTool())

    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=registry,
        trace_store=trace_store,
        checkpointer=build_memory_checkpointer(),
        require_sql_approval=True,
    )
    config = {
        "configurable": {
            "thread_id": "reject-approval-thread",
        }
    }
    state = {
        "session_id": "reject-approval-session",
        "trace_id": "reject-approval-trace",
        "thread_id": "reject-approval-thread",
        "user_query": "销售额最高的商品是什么？",
        "messages": [
            {
                "role": "user",
                "content": "销售额最高的商品是什么？",
            }
        ],
        "iteration": 0,
        "max_iterations": 3,
        "errors": [],
        "tool_results": [],
        "evidence": [],
    }

    paused = graph.invoke(state, config=config)
    assert paused["__interrupt__"]

    result = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "reason": "未获得授权",
            }
        ),
        config=config,
    )

    assert result["approval_status"] == "rejected"
    assert result["errors"][-1]["category"] == "approval"
    assert result["final_answer"]

    events = trace_store.list_by_trace("reject-approval-trace")
    assert "sql_query" not in [event.name for event in events]
