import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from graph.app import build_agent_graph
from graph.checkpointer import build_memory_checkpointer
from scripts.init_sqlite import init_sqlite


CASES = {
    "handbook": "根据 GitLab handbook，团队沟通的核心原则是什么？",
    "product": "根据 Mattermost handbook，产品管理团队主要关注什么？",
    "sql": "销售额最高的商品是什么？",
}


def run_case(case_name: str, query: str) -> dict:
    settings = load_settings()
    if settings.llm.provider != "qwen_api":
        raise RuntimeError(
            f"runtime provider must be qwen_api, got {settings.llm.provider}"
        )

    graph = build_agent_graph(
        settings=settings,
        checkpointer=build_memory_checkpointer(),
        require_sql_approval=False,
    )
    run_id = uuid4().hex[:8]
    state = {
        "session_id": f"qwen-business-{case_name}-{run_id}",
        "trace_id": f"qwen-business-trace-{run_id}",
        "thread_id": f"qwen-business-thread-{run_id}",
        "user_query": query,
        "messages": [{"role": "user", "content": query}],
        "iteration": 0,
        "max_iterations": settings.agent.max_iterations,
        "errors": [],
        "tool_results": [],
        "evidence": [],
    }
    started = perf_counter()
    output = graph.invoke(
        state,
        config={"configurable": {"thread_id": state["thread_id"]}},
    )
    latency_ms = int((perf_counter() - started) * 1000)

    return {
        "case": case_name,
        "query": query,
        "latency_ms": latency_ms,
        "selected_tools": output.get("selected_tools", []),
        "final_answer": output.get("final_answer", ""),
        "evidence_count": len(output.get("evidence", [])),
        "sources": [item.get("source") for item in output.get("evidence", [])],
        "errors": output.get("errors", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=[*CASES.keys(), "all"], default="handbook")
    parser.add_argument("--output", default="eval/reports/qwen_business_smoke.json")
    args = parser.parse_args()

    init_sqlite()
    case_names = list(CASES) if args.case == "all" else [args.case]
    results = [run_case(name, CASES[name]) for name in case_names]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for result in results:
        print(
            f"case={result['case']} "
            f"latency_ms={result['latency_ms']} "
            f"tools={result['selected_tools']} "
            f"evidence_count={result['evidence_count']}",
            flush=True,
        )
        print(f"answer={result['final_answer']}", flush=True)
        if result["errors"]:
            print(f"errors={result['errors']}", flush=True)

    if not all(result["final_answer"] for result in results):
        raise SystemExit(1)

    print(f"output={output_path}")
    print("smoke_qwen_business=ready")


if __name__ == "__main__":
    main()