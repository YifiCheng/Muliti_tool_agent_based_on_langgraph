from observer.schema import TraceEvent
from tools.base import Evidence, ToolRequest, ToolResult


def test_tool_schema():
    request = ToolRequest(query="hello", session_id="demo")
    evidence = Evidence(source="doc1", content="policy text", score=0.9)
    result = ToolResult(
        tool_name="mock_search",
        success=True,
        content="answer",
        evidence=[evidence],
    )

    assert request.query == "hello"
    assert result.evidence[0].source == "doc1"


def test_trace_schema():
    event = TraceEvent(
        trace_id="trace-1",
        session_id="demo",
        event_type="node",
        name="plan",
    )

    assert event.status == "success"