import json
import sqlite3
from pathlib import Path
from typing import Any

from observer.schema import TraceEvent
from observer.trace_store import TraceStore


class SQLiteTraceStore(TraceStore):
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trace_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_summary TEXT NOT NULL DEFAULT '',
                    output_summary TEXT NOT NULL DEFAULT '',
                    latency_ms INTEGER,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trace_events_session_id ON trace_events(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trace_events_trace_id ON trace_events(trace_id)"
            )

    def append(self, event: TraceEvent) -> None:
        self.init()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trace_events (
                    trace_id,
                    session_id,
                    event_type,
                    name,
                    status,
                    input_summary,
                    output_summary,
                    latency_ms,
                    metadata_json,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.trace_id,
                    event.session_id,
                    event.event_type,
                    event.name,
                    event.status,
                    event.input_summary,
                    event.output_summary,
                    event.latency_ms,
                    json.dumps(event.metadata, ensure_ascii=False),
                    event.error,
                ),
            )

    def list_by_session(self, session_id: str, limit: int = 100) -> list[TraceEvent]:
        self.init()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT trace_id, session_id, event_type, name, status,
                       input_summary, output_summary, latency_ms, metadata_json, error
                FROM trace_events
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def list_by_trace(self, trace_id: str, limit: int = 100) -> list[TraceEvent]:
        self.init()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT trace_id, session_id, event_type, name, status,
                       input_summary, output_summary, latency_ms, metadata_json, error
                FROM trace_events
                WHERE trace_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (trace_id, limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _row_to_event(self, row: tuple[Any, ...]) -> TraceEvent:
        return TraceEvent(
            trace_id=row[0],
            session_id=row[1],
            event_type=row[2],
            name=row[3],
            status=row[4],
            input_summary=row[5],
            output_summary=row[6],
            latency_ms=row[7],
            metadata=json.loads(row[8] or "{}"),
            error=row[9],
        )