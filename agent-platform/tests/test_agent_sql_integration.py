from graph.app import build_agent_graph
from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from observer.sqlite_store import SQLiteTraceStore
from tools.mock_tools import MockCalculatorTool
from tools.registry import ToolRegistry
from tools.sql_tool import SQLiteExecutor, SQLQueryTool

from tests.test_sql_tool import create_test_db


def test_agent_can_call_sql_query_tool(tmp_path):
    registry = ToolRegistry()
    registry.register(SQLQueryTool(SQLiteExecutor(create_test_db(tmp_path))))
    registry.register(MockCalculatorTool())

    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=registry,
        trace_store=trace_store,
    )

    result = graph.invoke(
        {
            "session_id": "session-sql",
            "trace_id": "trace-sql",
            "user_query": "销售额最高的商品是什么？",
            "messages": [{"role": "user", "content": "销售额最高的商品是什么？"}],
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
        }
    )

    assert result["selected_tools"] == ["sql_query"]
    assert result["tool_results"][0]["metadata"]["rows"][0]["product_name"] == "智能客服套餐"

    events = trace_store.list_by_trace("trace-sql")
    assert "sql_query" in [event.name for event in events]