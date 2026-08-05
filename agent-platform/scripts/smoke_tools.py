import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from observer.sqlite_store import SQLiteTraceStore
from tools.base import ToolRequest
from tools.mock_tools import build_mock_registry
from tools.runner import run_tool_safely


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", default="mock_document_search")
    parser.add_argument("--query", default="报销超过 5000 元需要谁审批？")
    parser.add_argument("--session-id", default="tool-smoke-session")
    parser.add_argument("--trace-id", default="tool-smoke-trace")
    args = parser.parse_args()

    settings = load_settings()
    trace_store = SQLiteTraceStore(settings.observer.sqlite_path)
    registry = build_mock_registry()
    tool = registry.get(args.tool)

    result = run_tool_safely(
        tool,
        ToolRequest(
            query=args.query,
            session_id=args.session_id,
            trace_id=args.trace_id,
        ),
        trace_store=trace_store,
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
