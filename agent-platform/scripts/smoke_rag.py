import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from rag.build_index import build_retriever
from tools.base import ToolRequest
from tools.document_search import DocumentSearchTool


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    settings = load_settings()
    tool = DocumentSearchTool(build_retriever(settings))
    result = tool.run(
        ToolRequest(
            query=args.query,
            session_id="rag-smoke-session",
            params={"top_k": args.top_k},
        )
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()