import pytest

from observer.schema import TraceEvent
from observer.sqlite_store import SQLiteTraceStore
from observer.trace_store import trace_span


def test_sqlite_trace_store_append_and_query(tmp_path):
    db_path = tmp_path / "traces.db"
    store = SQLiteTraceStore(db_path)

    event = TraceEvent(
        trace_id="trace-1",
        session_id="session-1",
        event_type="node",
        name="plan",
        input_summary="user asked policy question",
        output_summary="selected document_search",
        latency_ms=12,
        metadata={"iteration": 1},
    )

    store.append(event)

    by_session = store.list_by_session("session-1")
    by_trace = store.list_by_trace("trace-1")

    assert len(by_session) == 1
    assert len(by_trace) == 1
    assert by_session[0].name == "plan"
    assert by_session[0].metadata["iteration"] == 1


def test_trace_span_success(tmp_path):
    store = SQLiteTraceStore(tmp_path / "traces.db")

    with trace_span(
        store,
        trace_id="trace-2",
        session_id="session-2",
        event_type="tool",
        name="mock_search",
        input_summary="query",
    ) as span:
        span["output_summary"] = "found 1 document"
        span["metadata"]["top_k"] = 1

    events = store.list_by_trace("trace-2")

    assert len(events) == 1
    assert events[0].status == "success"
    assert events[0].latency_ms is not None
    assert events[0].metadata["top_k"] == 1


def test_trace_span_failed(tmp_path):
    store = SQLiteTraceStore(tmp_path / "traces.db")

    with pytest.raises(ValueError):
        with trace_span(
            store,
            trace_id="trace-3",
            session_id="session-3",
            event_type="tool",
            name="broken_tool",
        ):
            raise ValueError("tool failed")

    events = store.list_by_trace("trace-3")

    assert len(events) == 1
    assert events[0].status == "failed"
    assert "tool failed" in events[0].error