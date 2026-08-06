from graph.app import build_agent_graph
from graph.checkpointer import build_memory_checkpointer
from langgraph.types import Command
from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from tools.mock_tools import build_mock_registry


def initial_state(query: str) -> dict:
    return {
        "session_id": "checkpoint-session",
        "trace_id": "checkpoint-trace-1",
        "thread_id": "checkpoint-thread-1",
        "user_query": query,
        "messages": [{"role": "user", "content": query}],
        "iteration": 0,
        "max_iterations": 3,
        "errors": [],
        "tool_results": [],
        "evidence": [],
    }


def test_same_thread_can_read_latest_state():
    checkpointer = build_memory_checkpointer()
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=build_mock_registry(),
        checkpointer=checkpointer,
    )
    config = {
        "configurable": {
            "thread_id": "checkpoint-thread-1",
        }
    }

    result = graph.invoke(
        initial_state("报销审批规则"),
        config=config,
    )
    snapshot = graph.get_state(config)

    assert result["final_answer"]
    assert snapshot.values["session_id"] == "checkpoint-session"
    assert snapshot.values["iteration"] >= 1


def test_different_threads_do_not_share_state():
    checkpointer = build_memory_checkpointer()
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=build_mock_registry(),
        checkpointer=checkpointer,
    )

    graph.invoke(
        initial_state("报销审批规则"),
        config={"configurable": {"thread_id": "thread-a"}},
    )
    empty_snapshot = graph.get_state(
        {"configurable": {"thread_id": "thread-b"}}
    )

    assert empty_snapshot.values == {}


def test_interrupt_can_resume_with_same_thread(tmp_path):
    from langgraph.checkpoint.memory import MemorySaver
    from tests.test_sql_tool import create_test_db
    from tools.mock_tools import MockCalculatorTool
    from tools.registry import ToolRegistry
    from tools.sql_tool import SQLQueryTool, SQLiteExecutor

    checkpointer = MemorySaver()
    registry = ToolRegistry()
    registry.register(SQLQueryTool(SQLiteExecutor(create_test_db(tmp_path))))
    registry.register(MockCalculatorTool())
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=registry,
        checkpointer=checkpointer,
        require_sql_approval=True,
    )
    config = {
        "configurable": {
            "thread_id": "approval-thread-1",
        }
    }

    paused = graph.invoke(
        initial_state("销售额最高的商品是什么？"),
        config=config,
    )

    assert paused["__interrupt__"]
    resumed = graph.invoke(
        Command(resume={"decision": "approve", "reason": "test approval"}),
        config=config,
    )

    assert resumed["final_answer"]