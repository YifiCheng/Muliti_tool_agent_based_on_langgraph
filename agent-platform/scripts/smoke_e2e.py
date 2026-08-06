import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph.app import run_agent
from scripts.init_sqlite import init_sqlite


SCENARIOS = [
    {
        "name": "rag",
        "query": "报销超过 5000 元需要谁审批？",
    },
    {
        "name": "sql",
        "query": "销售额最高的商品是什么？",
    },
    {
        "name": "calculator",
        "query": "12 * 8",
    },
]


def main() -> None:
    init_sqlite()
    summaries = []

    for scenario in SCENARIOS:
        name = scenario["name"]
        result = run_agent(
            scenario["query"],
            session_id=f"step9-{name}-session",
            trace_id=f"step9-{name}-trace",
        )
        tool_results = result.get("tool_results", [])
        summaries.append(
            {
                "scenario": name,
                "selected_tools": result.get("selected_tools", []),
                "tool_success": [
                    item.get("success") for item in tool_results
                ],
                "iteration": result.get("iteration"),
                "reflection": result.get("reflection", {}),
                "error_count": len(result.get("errors", [])),
                "has_final_answer": bool(result.get("final_answer")),
            }
        )

    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()