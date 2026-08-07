from pathlib import Path
from uuid import uuid4

import yaml
from langgraph.types import Command

from config.settings import load_settings
from eval.metrics import build_report, score_case
from eval.schema import EvalCase, EvalReport
from graph.app import build_agent_graph
from graph.checkpointer import build_memory_checkpointer
from scripts.init_sqlite import init_sqlite


def load_cases(path: str | Path) -> list[EvalCase]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [EvalCase.model_validate(item) for item in raw["cases"]]


def run_eval(cases: list[EvalCase]) -> EvalReport:
    init_sqlite()
    settings = load_settings()
    checkpointer = build_memory_checkpointer()
    graph_without_approval = build_agent_graph(
        settings=settings,
        checkpointer=checkpointer,
        require_sql_approval=False,
    )
    graph_with_approval = build_agent_graph(
        settings=settings,
        checkpointer=checkpointer,
        require_sql_approval=True,
    )

    results = []
    for case in cases:
        run_id = uuid4().hex[:8]
        thread_id = f"eval-{case.case_id}-{run_id}"
        state = {
            "session_id": thread_id,
            "trace_id": f"trace-{thread_id}",
            "thread_id": thread_id,
            "user_query": case.query,
            "messages": [{"role": "user", "content": case.query}],
            "iteration": 0,
            "max_iterations": case.max_iterations,
            "errors": [],
            "tool_results": [],
            "evidence": [],
        }
        config = {"configurable": {"thread_id": thread_id}}
        graph = graph_with_approval if case.require_approval else graph_without_approval
        output = graph.invoke(state, config=config)

        if output.get("__interrupt__"):
            if case.approval_decision is None:
                output = {
                    **output,
                    "final_answer": "",
                    "approval_status": "interrupted",
                }
            else:
                output = graph.invoke(
                    Command(
                        resume={
                            "decision": case.approval_decision,
                            "reason": "eval decision",
                        }
                    ),
                    config=config,
                )

        results.append(score_case(case, output))

    return build_report(results)