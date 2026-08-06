import sqlite3
from pathlib import Path
from typing import Any

from config.settings import Settings


def build_memory_checkpointer() -> Any:
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()


def build_sqlite_checkpointer(settings: Settings) -> Any:
    from langgraph.checkpoint.sqlite import SqliteSaver

    db_path = Path(settings.agent.checkpoint_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        db_path,
        check_same_thread=False,
    )
    return SqliteSaver(connection)