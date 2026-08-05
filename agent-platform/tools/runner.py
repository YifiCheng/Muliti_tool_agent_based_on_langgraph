from observer.trace_store import TraceStore, trace_span
from tools.base import BaseTool, ToolRequest, ToolResult


def run_tool_safely(
    tool: BaseTool,
    request: ToolRequest,
    trace_store: TraceStore | None = None,
) -> ToolResult:
    if trace_store is None or request.trace_id is None:
        return _run_without_trace(tool, request)

    try:
        with trace_span(
            trace_store,
            trace_id=request.trace_id,
            session_id=request.session_id,
            event_type="tool",
            name=tool.name,
            input_summary=_summarize_input(request),
        ) as span:
            result = _run_without_trace(tool, request)
            span["output_summary"] = _summarize_output(result)
            span["metadata"]["success"] = result.success
            span["metadata"]["evidence_count"] = len(result.evidence)
            return result
    except Exception as exc:
        return ToolResult(
            tool_name=tool.name,
            success=False,
            error=str(exc),
        )


def _run_without_trace(tool: BaseTool, request: ToolRequest) -> ToolResult:
    try:
        return tool.run(request)
    except Exception as exc:
        return ToolResult(
            tool_name=tool.name,
            success=False,
            error=str(exc),
        )


def _summarize_input(request: ToolRequest) -> str:
    return request.query[:200]


def _summarize_output(result: ToolResult) -> str:
    if result.success:
        return result.content[:200]
    return (result.error or "")[:200]