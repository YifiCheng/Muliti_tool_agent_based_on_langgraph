from config.settings import Settings
from rag.build_index import build_retriever
from tools.document_search import DocumentSearchTool
from tools.mock_tools import MockCalculatorTool, MockSQLTool
from tools.registry import ToolRegistry


def build_agent_registry(settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(DocumentSearchTool(build_retriever(settings)))
    registry.register(MockSQLTool())
    registry.register(MockCalculatorTool())
    return registry