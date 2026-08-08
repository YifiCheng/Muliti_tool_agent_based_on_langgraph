from config.settings import Settings
from rag.build_index import build_retriever
from rag.query_translation import NoopQueryTranslator, RuleBasedQueryTranslator
from tools.document_search import DocumentSearchTool
from tools.mock_tools import MockCalculatorTool
from tools.registry import ToolRegistry
from tools.sql_tool import SQLiteExecutor, SQLQueryTool


def build_query_translator(settings: Settings):
    if not settings.rag.enable_query_translation:
        return NoopQueryTranslator()

    if settings.rag.query_translation_strategy == "rule_based":
        return RuleBasedQueryTranslator()

    return NoopQueryTranslator()


def build_agent_registry(settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        DocumentSearchTool(
            build_retriever(settings),
            translator=build_query_translator(settings),
        )
    )
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