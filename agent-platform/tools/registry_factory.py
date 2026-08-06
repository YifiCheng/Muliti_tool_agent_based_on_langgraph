from config.settings import Settings
from rag.build_index import build_retriever
from tools.document_search import DocumentSearchTool
from tools.mock_tools import MockCalculatorTool
from tools.sql_tool import SQLiteExecutor, SQLQueryTool
from tools.registry import ToolRegistry


def build_agent_registry(settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(DocumentSearchTool(build_retriever(settings)))
    registry.register(
        SQLQueryTool(
            SQLiteExecutor(
                settings.sql.sqlite_path,
                max_rows=settings.sql.max_rows,
            )
        )
    )
    registry.register(MockCalculatorTool())
    return registry