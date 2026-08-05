import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph.app import run_agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="报销超过 5000 元需要谁审批？")
    parser.add_argument("--session-id", default="graph-smoke-session")
    parser.add_argument("--trace-id", default="graph-smoke-trace")
    parser.add_argument("--max-iterations", type=int, default=3)
    args = parser.parse_args()

    result = run_agent(
        args.query,
        session_id=args.session_id,
        trace_id=args.trace_id,
        max_iterations=args.max_iterations,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()