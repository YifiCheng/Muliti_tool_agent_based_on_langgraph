from abc import ABC, abstractmethod
import time
from contextlib import contextmanager
from typing import Generator

from observer.schema import TraceEvent

class TraceStore(ABC):
    @abstractmethod
    def init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def append(self, event: TraceEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_by_session(self, session_id: str, limit: int = 100) -> list[TraceEvent]:
        raise NotImplementedError

    @abstractmethod
    def list_by_trace(self, trace_id: str, limit: int = 100) -> list[TraceEvent]:
        raise NotImplementedError

@contextmanager
def trace_span(
    store: TraceStore,
    *,
    trace_id: str,
    session_id: str,
    event_type: str,
    name: str,
    input_summary: str = "",
    metadata: dict | None = None,
) -> Generator[dict, None, None]:
    start = time.perf_counter()
    span_result = {"output_summary": "", "metadata": metadata or {}}
    try:
        yield span_result
        status = "success"
        error = None
    except Exception as exc:
        status = "failed"
        error = str(exc)
        raise
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        store.append(
            TraceEvent(
                trace_id=trace_id,
                session_id=session_id,
                event_type=event_type,  # type: ignore[arg-type]
                name=name,
                status=status,  # type: ignore[arg-type]
                input_summary=input_summary,
                output_summary=span_result.get("output_summary", ""),
                latency_ms=latency_ms,
                metadata=span_result.get("metadata", {}),
                error=error,
            )
        )
