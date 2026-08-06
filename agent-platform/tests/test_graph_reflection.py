from graph.app import build_agent_graph
from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from observer.sqlite_store import SQLiteTraceStore
from tools.mock_tools import build_mock_registry


class ReflectionRetryProvider(MockLLMProvider):
    def __init__(self) -> None:
        self.reflection_calls = 0

    def chat_json(self, messages: list[dict], schema_name: str) -> dict:
        if schema_name == "plan":
            return {
                "tools": ["mock_document_search"],
                "reason": "reflection integration test plan",
            }

        if schema_name == "reflection":
            self.reflection_calls += 1
            if self.reflection_calls == 1:
                return {
                    "is_sufficient": False,
                    "missing_info": ["需要补充审批条件"],
                    "next_action": "retrieve_more",
                    "replan_query": "补充检索报销审批条件",
                    "reason": "first reflection requests more evidence",
                }
            return {
                "is_sufficient": True,
                "missing_info": [],
                "next_action": "answer",
                "reason": "second reflection accepts evidence",
            }

        return super().chat_json(messages, schema_name)


def test_graph_reflection_retries_once_and_records_source(tmp_path):
    provider = ReflectionRetryProvider()
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(provider),
        registry=build_mock_registry(),
        trace_store=trace_store,
    )

    result = graph.invoke(
        {
            "session_id": "reflection-session",
            "trace_id": "reflection-trace",
            "user_query": "报销审批规则",
            "messages": [{"role": "user", "content": "报销审批规则"}],
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
        }
    )

    assert result["iteration"] == 2
    assert result["reflection"]["is_sufficient"] is True
    assert result["reflection"]["source"] == "llm"
    assert result["reflection"]["next_action"] == "answer"

    events = trace_store.list_by_trace("reflection-trace")
    reflect_events = [event for event in events if event.name == "reflect"]
    assert len(reflect_events) == 2
    assert reflect_events[-1].metadata["source"] == "llm"


def test_graph_reflection_stops_at_max_iterations(tmp_path):
    provider = ReflectionRetryProvider()
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")
    graph = build_agent_graph(
        llm=LLMClient(provider),
        registry=build_mock_registry(),
        trace_store=trace_store,
    )

    result = graph.invoke(
        {
            "session_id": "limit-session",
            "trace_id": "limit-trace",
            "user_query": "报销审批规则",
            "messages": [{"role": "user", "content": "报销审批规则"}],
            "iteration": 0,
            "max_iterations": 1,
            "errors": [],
        }
    )

    assert result["iteration"] == 1
    assert result["final_answer"]