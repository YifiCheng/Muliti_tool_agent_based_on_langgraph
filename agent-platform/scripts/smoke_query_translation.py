import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.query_translation import RuleBasedQueryTranslator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default="GitLab handbook 中如何描述沟通方式？",
    )
    args = parser.parse_args()

    result = RuleBasedQueryTranslator().translate(args.query)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))

    if result.original_query != args.query:
        raise RuntimeError("original query changed unexpectedly")
    if "沟通" in args.query and "communication" not in result.search_query:
        raise RuntimeError("expected communication translation")

    print("smoke_query_translation=ready")


if __name__ == "__main__":
    main()