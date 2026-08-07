from collections import defaultdict

from eval.schema import EvalCase, EvalCaseResult, EvalReport


def contains_all_keywords(text: str, keywords: list[str]) -> bool:
    return all(keyword in text for keyword in keywords)


def tool_match(selected_tools: list[str], expected_tools: list[str]) -> bool:
    return all(tool in selected_tools for tool in expected_tools)


def has_evidence(state: dict) -> bool:
    return bool(state.get("evidence", []))


def score_case(case: EvalCase, state: dict) -> EvalCaseResult:
    selected_tools = state.get("selected_tools", [])
    final_answer = state.get("final_answer", "") or ""

    checks = {
        "tool_match": tool_match(selected_tools, case.expected_tools),
        "keyword_match": contains_all_keywords(final_answer, case.expected_keywords),
        "has_final_answer": bool(final_answer),
    }

    if case.require_evidence:
        checks["evidence_present"] = has_evidence(state)

    if case.require_approval:
        checks["approval_status"] = state.get("approval_status") == case.approval_decision + "d"
        if case.approval_decision == "approve":
            checks["sql_executed"] = any(
                result.get("tool_name") == "sql_query"
                and result.get("success") is True
                for result in state.get("tool_results", [])
            )

    passed = all(checks.values())
    score = sum(1 for value in checks.values() if value) / max(len(checks), 1)
    errors = [name for name, ok in checks.items() if not ok]

    return EvalCaseResult(
        case_id=case.case_id,
        category=case.category,
        query=case.query,
        passed=passed,
        score=score,
        selected_tools=selected_tools,
        final_answer=final_answer,
        checks=checks,
        errors=errors,
        metadata={
            "iteration": state.get("iteration"),
            "approval_status": state.get("approval_status"),
        },
    )


def build_report(results: list[EvalCaseResult]) -> EvalReport:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    average_score = (
        sum(result.score for result in results) / total
        if total
        else 0.0
    )

    grouped: dict[str, list[EvalCaseResult]] = defaultdict(list)
    for result in results:
        grouped[result.category].append(result)

    by_category = {}
    for category, items in grouped.items():
        by_category[category] = {
            "total": len(items),
            "passed": sum(1 for item in items if item.passed),
            "pass_rate": (
                sum(1 for item in items if item.passed) / len(items)
                if items
                else 0.0
            ),
            "average_score": sum(item.score for item in items) / len(items),
        }

    return EvalReport(
        total=total,
        passed=passed,
        pass_rate=passed / total if total else 0.0,
        average_score=average_score,
        by_category=by_category,
        results=results,
    )