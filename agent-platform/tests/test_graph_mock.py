from graph.app import build_agent_graph
from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from observer.sqlite_store import SQLiteTraceStore
from tools.mock_tools import build_mock_registry


def test_graph_runs_document_search_flow(tmp_path):
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=build_mock_registry(),
        trace_store=trace_store,
    )

    result = graph.invoke(
        {
            "session_id": "session-1",
            "trace_id": "trace-1",
            "user_query": "报销超过 5000 元需要谁审批？",
            "messages": [{"role": "user", "content": "报销超过 5000 元需要谁审批？"}],
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
        }
    )

    assert result["selected_tools"] == ["mock_document_search"]
    assert result["tool_results"][0]["success"] is True
    assert result["evidence"]
    assert result["reflection"]["next_action"] == "answer"
    assert result["final_answer"]


def test_graph_runs_sql_flow(tmp_path):
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=build_mock_registry(),
        trace_store=trace_store,
    )

    result = graph.invoke(
        {
            "session_id": "session-2",
            "trace_id": "trace-2",
            "user_query": "销售额最高的商品是什么？",
            "messages": [{"role": "user", "content": "销售额最高的商品是什么？"}],
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
        }
    )

    assert result["selected_tools"] == ["mock_sql"]
    assert result["tool_results"][0]["metadata"]["row_count"] == 2
    assert result["final_answer"]


def test_graph_records_node_and_tool_traces(tmp_path):
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(MockLLMProvider()),
        registry=build_mock_registry(),
        trace_store=trace_store,
    )

    graph.invoke(
        {
            "session_id": "session-3",
            "trace_id": "trace-3",
            "user_query": "报销审批规则",
            "messages": [{"role": "user", "content": "报销审批规则"}],
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
        }
    )

    events = trace_store.list_by_trace("trace-3")
    names = [event.name for event in events]

    assert "plan" in names
    assert "mock_document_search" in names
    assert "reflect" in names
    assert "answer" in names

class RetryOnceMockProvider(MockLLMProvider):
    def __init__(self) -> None:
        self.reflect_calls = 0

    def chat_json(self, messages: list[dict], schema_name: str) -> dict:
        if schema_name == "plan":
            return {
                "tools": ["mock_document_search"],
                "reason": "retry test plan",
            }

        if schema_name == "reflection":
            self.reflect_calls += 1
            if self.reflect_calls == 1:
                return {
                    "is_sufficient": False,
                    "missing_info": ["need more evidence"],
                    "next_action": "retrieve_more",
                    "replan_query": "补充检索报销审批规则",
                    "reason": "retry once",
                }
            return {
                "is_sufficient": True,
                "missing_info": [],
                "next_action": "answer",
                "reason": "enough after retry",
            }

        return {}


def test_graph_can_retry_once_after_reflection(tmp_path):
    provider = RetryOnceMockProvider()
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(provider),
        registry=build_mock_registry(),
        trace_store=trace_store,
    )

    result = graph.invoke(
        {
            "session_id": "session-4",
            "trace_id": "trace-4",
            "user_query": "需要补充的报销审批规则",
            "messages": [{"role": "user", "content": "需要补充的报销审批规则"}],
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
        }
    )

    assert result["iteration"] == 2
    assert result["reflection"]["next_action"] == "answer"
    assert result["final_answer"]