from graph.app import build_agent_graph
from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from observer.sqlite_store import SQLiteTraceStore
from tools.base import BaseTool, Evidence, ToolRequest, ToolResult
from tools.registry import ToolRegistry


class QueryAwareDocumentTool(BaseTool):
    name = "mock_document_search"
    description = "Return evidence containing the actual tool query."

    def run(self, request: ToolRequest) -> ToolResult:
        evidence = Evidence(
            source=f"query:{request.query}",
            content=f"evidence for {request.query}",
        )
        return ToolResult(
            tool_name=self.name,
            success=True,
            content="query-aware evidence",
            evidence=[evidence],
        )


class ReplanProvider(MockLLMProvider):
    def __init__(self) -> None:
        self.plan_messages: list[str] = []
        self.reflection_calls = 0

    def chat_json(self, messages: list[dict], schema_name: str) -> dict:
        if schema_name == "plan":
            self.plan_messages.append(messages[-1]["content"])
            return {
                "tools": ["mock_document_search"],
                "reason": "replan integration test",
            }

        if schema_name == "reflection":
            self.reflection_calls += 1
            if self.reflection_calls == 1:
                return {
                    "is_sufficient": False,
                    "missing_info": ["审批角色"],
                    "next_action": "retrieve_more",
                    "replan_query": "补充检索超过 5000 元的审批角色",
                    "reason": "need a more specific query",
                }
            return {
                "is_sufficient": True,
                "missing_info": [],
                "next_action": "answer",
                "reason": "accumulated evidence is sufficient",
            }

        return super().chat_json(messages, schema_name)


class UnknownToolProvider(MockLLMProvider):
    def chat_json(self, messages: list[dict], schema_name: str) -> dict:
        if schema_name == "plan":
            return {
                "tools": ["not_registered"],
                "reason": "test unknown tool",
            }
        return super().chat_json(messages, schema_name)


def build_query_aware_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(QueryAwareDocumentTool())
    return registry


def test_replan_query_is_used_by_second_plan_and_tool(tmp_path):
    provider = ReplanProvider()
    graph = build_agent_graph(
        llm=LLMClient(provider),
        registry=build_query_aware_registry(),
        trace_store=SQLiteTraceStore(tmp_path / "traces.db"),
    )

    result = graph.invoke(
        {
            "session_id": "replan-session",
            "trace_id": "replan-trace",
            "user_query": "报销审批规则",
            "active_query": "报销审批规则",
            "replan_query": None,
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
            "tool_results": [],
            "evidence": [],
        }
    )

    assert result["iteration"] == 2
    assert "报销审批规则" in provider.plan_messages[0]
    assert "补充检索超过 5000 元的审批角色" in provider.plan_messages[1]
    assert result["active_query"] == "补充检索超过 5000 元的审批角色"

    evidence_contents = [item["content"] for item in result["evidence"]]
    assert "evidence for 报销审批规则" in evidence_contents
    assert (
        "evidence for 补充检索超过 5000 元的审批角色"
        in evidence_contents
    )


def test_replan_accumulates_two_tool_results(tmp_path):
    graph = build_agent_graph(
        llm=LLMClient(ReplanProvider()),
        registry=build_query_aware_registry(),
        trace_store=SQLiteTraceStore(tmp_path / "traces.db"),
    )

    result = graph.invoke(
        {
            "session_id": "history-session",
            "trace_id": "history-trace",
            "user_query": "报销审批规则",
            "iteration": 0,
            "max_iterations": 3,
            "errors": [],
            "tool_results": [],
            "evidence": [],
        }
    )

    assert len(result["tool_results"]) == 2
    assert len(result["evidence"]) == 2


def test_unknown_tool_is_recorded_in_errors(tmp_path):
    graph = build_agent_graph(
        llm=LLMClient(UnknownToolProvider()),
        registry=ToolRegistry(),
        trace_store=SQLiteTraceStore(tmp_path / "traces.db"),
    )

    result = graph.invoke(
        {
            "session_id": "error-session",
            "trace_id": "error-trace",
            "user_query": "测试不存在工具",
            "iteration": 0,
            "max_iterations": 1,
            "errors": [],
            "tool_results": [],
            "evidence": [],
        }
    )

    assert result["tool_results"][0]["success"] is False
    assert result["errors"][0]["category"] == "tool_lookup"
    assert result["final_answer"]