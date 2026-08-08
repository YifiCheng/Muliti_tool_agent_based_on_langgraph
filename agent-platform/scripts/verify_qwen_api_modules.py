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
from llm.client import build_llm_client
from scripts.init_sqlite import init_sqlite


def run_check(name: str, fn):
    started = perf_counter()
    try:
        result = fn()
        return {
            "name": name,
            "success": True,
            "latency_ms": int((perf_counter() - started) * 1000),
            "result": result,
            "error": None,
        }
    except Exception as exc:
        return {
            "name": name,
            "success": False,
            "latency_ms": int((perf_counter() - started) * 1000),
            "result": None,
            "error": str(exc),
        }


def qwen_chat_check(settings):
    client = build_llm_client(settings)
    answer = client.chat(
        [{"role": "user", "content": "用一句话说明 LangGraph 的作用。"}],
        temperature=0.2,
    )
    return {"answer": answer[:300]}


def qwen_json_plan_check(settings):
    client = build_llm_client(settings)
    data = client.chat_json(
        [
            {
                "role": "user",
                "content": (
                    "请返回 JSON：{\"tools\":[\"document_search\"],"
                    "\"reason\":\"test\"}"
                ),
            }
        ],
        schema_name="plan",
    )
    return {"json": data}


def graph_document_check(settings):
    graph = build_agent_graph(
        settings=settings,
        checkpointer=build_memory_checkpointer(),
        require_sql_approval=False,
    )
    run_id = uuid4().hex[:8]
    state = {
        "session_id": f"qwen-api-graph-{run_id}",
        "trace_id": f"qwen-api-trace-{run_id}",
        "thread_id": f"qwen-api-thread-{run_id}",
        "user_query": "报销超过 5000 元需要谁审批？",
        "messages": [
            {"role": "user", "content": "报销超过 5000 元需要谁审批？"}
        ],
        "iteration": 0,
        "max_iterations": 2,
        "errors": [],
        "tool_results": [],
        "evidence": [],
    }
    output = graph.invoke(
        state,
        config={"configurable": {"thread_id": state["thread_id"]}},
    )
    return {
        "selected_tools": output.get("selected_tools", []),
        "final_answer": (output.get("final_answer") or "")[:500],
        "evidence_count": len(output.get("evidence", [])),
        "errors": output.get("errors", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="eval/reports/qwen_api_validation.json",
    )
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="Write report even if some checks fail.",
    )
    args = parser.parse_args()

    init_sqlite()
    settings = load_settings()
    settings.llm.provider = "qwen_api"

    checks = [
        run_check("qwen_chat", lambda: qwen_chat_check(settings)),
        run_check("qwen_json_plan", lambda: qwen_json_plan_check(settings)),
        run_check("graph_document_query", lambda: graph_document_check(settings)),
    ]

    report = {
        "provider": "qwen_api",
        "model": settings.llm.qwen_api.model_env,
        "checks": checks,
        "passed": sum(1 for item in checks if item["success"]),
        "total": len(checks),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for item in checks:
        print(
            f"{item['name']} success={item['success']} "
            f"latency_ms={item['latency_ms']}"
        )
        if item["error"]:
            print(f"  error={item['error']}")

    print(f"output={output_path}")
    print("verify_qwen_api_modules=ready")

    if report["passed"] != report["total"] and not args.allow_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()