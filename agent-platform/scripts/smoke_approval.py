import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langgraph.types import Command

from config.settings import load_settings
from graph.app import build_agent_graph
from graph.checkpointer import build_memory_checkpointer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", choices=["approve", "reject"], default="approve")
    parser.add_argument("--reason", default="smoke test reviewed")
    parser.add_argument("--session-id", default="approval-smoke-session")
    parser.add_argument("--trace-id", default="approval-smoke-trace")
    parser.add_argument("--thread-id", default="approval-smoke-thread")
    parser.add_argument("--query", default="销售额最高的商品是什么？")
    args = parser.parse_args()

    settings = load_settings()
    graph = build_agent_graph(
        settings=settings,
        checkpointer=build_memory_checkpointer(),
        require_sql_approval=True,
    )
    config = {
        "configurable": {
            "thread_id": args.thread_id,
        }
    }
    initial_state = {
        "session_id": args.session_id,
        "trace_id": args.trace_id,
        "thread_id": args.thread_id,
        "user_query": args.query,
        "messages": [{"role": "user", "content": args.query}],
        "iteration": 0,
        "max_iterations": 3,
        "errors": [],
        "tool_results": [],
        "evidence": [],
    }

    paused = graph.invoke(initial_state, config=config)
    print("paused=", bool(paused.get("__interrupt__")))
    print(paused.get("__interrupt__"))

    resumed = graph.invoke(
        Command(
            resume={
                "decision": args.decision,
                "reason": args.reason,
            }
        ),
        config=config,
    )
    print("approval_status=", resumed["approval_status"])
    tool_results = resumed.get("tool_results", [])
    print("sql_executed=", bool(tool_results))
    print("sql_success=", tool_results[0]["success"] if tool_results else False)
    print("has_final_answer=", bool(resumed.get("final_answer")))


if __name__ == "__main__":
    main()