import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from rag.build_index import build_retriever
from rag.query_translation import NoopQueryTranslator, RuleBasedQueryTranslator
from tools.base import ToolRequest
from tools.document_search import DocumentSearchTool


def run_search(query: str, *, translated: bool, top_k: int) -> dict:
    settings = load_settings()
    settings = settings.model_copy(
        update={
            "rag": settings.rag.model_copy(
                update={"docs_dir": "data/public_docs/clean"}
            )
        }
    )
    translator = RuleBasedQueryTranslator() if translated else NoopQueryTranslator()
    tool = DocumentSearchTool(
        build_retriever(settings),
        translator=translator,
    )
    result = tool.run(
        ToolRequest(
            query=query,
            session_id="compare-public-rag-translation",
            params={"top_k": top_k},
        )
    )
    return result.model_dump()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default="GitLab handbook 中如何描述沟通方式？",
    )
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    without_translation = run_search(
        args.query,
        translated=False,
        top_k=args.top_k,
    )
    with_translation = run_search(
        args.query,
        translated=True,
        top_k=args.top_k,
    )

    output = {
        "query": args.query,
        "without_translation": {
            "metadata": without_translation["metadata"],
            "sources": [
                item["source"]
                for item in without_translation["evidence"]
            ],
        },
        "with_translation": {
            "metadata": with_translation["metadata"],
            "sources": [
                item["source"]
                for item in with_translation["evidence"]
            ],
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("compare_public_rag_translation=ready")


if __name__ == "__main__":
    main()