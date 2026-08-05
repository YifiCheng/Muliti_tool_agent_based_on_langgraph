from observer.sqlite_store import SQLiteTraceStore
from tools.base import BaseTool, ToolRequest, ToolResult
from tools.errors import ToolNotFoundError
from tools.mock_tools import MockCalculatorTool, build_mock_registry
from tools.registry import ToolRegistry
from tools.runner import run_tool_safely


def test_build_mock_registry():
    registry = build_mock_registry()
    assert registry.names() == [
        "mock_calculator",
        "mock_document_search",
        "mock_sql",
    ]


def test_registry_get_missing_tool():
    registry = ToolRegistry()
    try:
        registry.get("missing")
    except ToolNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("ToolNotFoundError was not raised")


def test_mock_document_search_returns_evidence():
    registry = build_mock_registry()
    tool = registry.get("mock_document_search")
    result = tool.run(ToolRequest(query="报销审批", session_id="s1"))

    assert result.success is True
    assert result.evidence
    assert result.evidence[0].source == "mock_policy.md#section_1"


def test_mock_sql_returns_rows():
    registry = build_mock_registry()
    tool = registry.get("mock_sql")
    result = tool.run(ToolRequest(query="销售额最高的商品", session_id="s1"))

    assert result.success is True
    assert result.metadata["row_count"] == 2


def test_mock_calculator():
    tool = MockCalculatorTool()
    result = tool.run(ToolRequest(query="1+2*3", session_id="s1"))

    assert result.success is True
    assert result.content == "7"


def test_mock_calculator_rejects_unsafe_expression():
    tool = MockCalculatorTool()
    result = run_tool_safely(
        tool,
        ToolRequest(query="__import__('os').system('dir')", session_id="s1"),
    )

    assert result.success is False
    assert "Only simple arithmetic" in result.error


def test_run_tool_safely_records_trace(tmp_path):
    registry = build_mock_registry()
    tool = registry.get("mock_document_search")
    trace_store = SQLiteTraceStore(tmp_path / "traces.db")

    result = run_tool_safely(
        tool,
        ToolRequest(
            query="报销审批",
            session_id="session-1",
            trace_id="trace-1",
        ),
        trace_store=trace_store,
    )

    events = trace_store.list_by_trace("trace-1")

    assert result.success is True
    assert len(events) == 1
    assert events[0].event_type == "tool"
    assert events[0].name == "mock_document_search"
    assert events[0].metadata["evidence_count"] == 1


class BrokenTool(BaseTool):
    name = "broken"
    description = "Always fails."

    def run(self, request: ToolRequest) -> ToolResult:
        raise RuntimeError("boom")


def test_run_tool_safely_wraps_error():
    result = run_tool_safely(
        BrokenTool(),
        ToolRequest(query="fail", session_id="s1"),
    )

    assert result.success is False
    assert "boom" in result.error