import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings, load_settings
from graph.app import build_agent_graph
from graph.checkpointer import build_memory_checkpointer
from llm.client import build_llm_client
from scripts.init_sqlite import init_sqlite


CASES = {
    "direct": "用一句话说明企业知识库 Agent 的作用。",
    "handbook": "根据 GitLab handbook，团队沟通的核心原则是什么？",
    "product": "根据 Mattermost handbook，产品管理团队主要关注什么？",
    "sql": "销售额最高的商品是什么？",
}


def settings_for_provider(base: Settings, provider: str) -> Settings:
    copied = base.model_copy(deep=True)
    copied.llm.provider = provider
    return copied


def run_direct(settings: Settings, prompt: str) -> dict:
    started = perf_counter()
    client = build_llm_client(settings)
    answer = client.chat(
        [{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return {
        "latency_ms": int((perf_counter() - started) * 1000),
        "answer": answer,
        "selected_tools": [],
        "evidence_count": 0,
        "sources": [],
        "errors": [],
    }


def run_agent_case(settings: Settings, case_name: str, query: str) -> dict:
    graph = build_agent_graph(
        settings=settings,
        checkpointer=build_memory_checkpointer(),
        require_sql_approval=False,
    )
    run_id = uuid4().hex[:8]
    state = {
        "session_id": f"compare-{settings.llm.provider}-{case_name}-{run_id}",
        "trace_id": f"compare-trace-{settings.llm.provider}-{run_id}",
        "thread_id": f"compare-thread-{settings.llm.provider}-{run_id}",
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
        "latency_ms": latency_ms,
        "answer": output.get("final_answer", ""),
        "selected_tools": output.get("selected_tools", []),
        "evidence_count": len(output.get("evidence", [])),
        "sources": [item.get("source") for item in output.get("evidence", [])],
        "errors": output.get("errors", []),
    }


def run_provider(provider: str, case_names: list[str]) -> list[dict]:
    base_settings = load_settings()
    settings = settings_for_provider(base_settings, provider)
    results = []
    for case_name in case_names:
        query = CASES[case_name]
        if case_name == "direct":
            result = run_direct(settings, query)
        else:
            result = run_agent_case(settings, case_name, query)
        results.append(
            {
                "provider": provider,
                "case": case_name,
                "query": query,
                **result,
            }
        )
        print(
            f"provider={provider} case={case_name} "
            f"latency_ms={result['latency_ms']} "
            f"tools={result['selected_tools']} "
            f"evidence_count={result['evidence_count']}",
            flush=True,
        )
    return results


def write_markdown(results: list[dict], output_path: Path) -> None:
    lines = [
        "# Qwen Provider Comparison",
        "",
        "| case | provider | latency_ms | tools | evidence_count | answer_preview |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for item in results:
        answer = item["answer"].replace("\n", " ")[:120]
        tools = ",".join(item["selected_tools"])
        lines.append(
            f"| {item['case']} | {item['provider']} | {item['latency_ms']} "
            f"| {tools} | {item['evidence_count']} | {answer} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `latency_ms` 包含 provider 调用、Agent 规划、工具执行和回答生成。",
            "- `direct` 只测试模型直连，不经过 Agent 工具链。",
            "- `handbook` / `product` / `sql` 测试真实 Agent 路径。",
            "- 回答质量需要结合 evidence、工具选择和 answer_preview 人工判断。",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["qwen_api", "remote_qwen"],
        choices=["qwen_api", "remote_qwen"],
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        default=["direct", "handbook", "sql"],
        choices=list(CASES),
    )
    parser.add_argument(
        "--json-output",
        default="eval/reports/qwen_provider_comparison.json",
    )
    parser.add_argument(
        "--md-output",
        default="eval/reports/qwen_provider_comparison.md",
    )
    args = parser.parse_args()

    init_sqlite()
    all_results = []
    for provider in args.providers:
        all_results.extend(run_provider(provider, args.cases))

    json_path = Path(args.json_output)
    md_path = Path(args.md_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown(all_results, md_path)

    print(f"json_output={json_path}")
    print(f"md_output={md_path}")
    print("compare_qwen_providers=ready")


if __name__ == "__main__":
    main()