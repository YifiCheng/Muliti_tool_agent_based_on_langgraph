from graph.state_utils import (
    append_tool_results,
    collect_tool_errors,
    get_active_query,
    merge_evidence,
)


def test_get_active_query_uses_user_query_first():
    state = {
        "user_query": "原始问题",
        "replan_query": None,
    }
    assert get_active_query(state) == "原始问题"


def test_get_active_query_uses_replan_query():
    state = {
        "user_query": "原始问题",
        "replan_query": "补充检索问题",
    }
    assert get_active_query(state) == "补充检索问题"


def test_append_tool_results_preserves_history():
    result = append_tool_results(
        [{"tool_name": "first"}],
        [{"tool_name": "second"}],
    )
    assert [item["tool_name"] for item in result] == ["first", "second"]


def test_merge_evidence_removes_exact_duplicates():
    evidence = {
        "source": "policy.md#1",
        "content": "审批规则",
    }
    result = merge_evidence([evidence], [evidence])
    assert result == [evidence]


def test_merge_evidence_keeps_different_chunks():
    result = merge_evidence(
        [{"source": "policy.md", "content": "第一段"}],
        [{"source": "policy.md", "content": "第二段"}],
    )
    assert len(result) == 2


def test_collect_tool_errors_creates_structured_error():
    errors = collect_tool_errors(
        [
            {
                "tool_name": "missing_tool",
                "success": False,
                "error": "Tool not found",
                "metadata": {"error_category": "tool_lookup"},
            }
        ],
        iteration=2,
    )

    assert errors[0]["category"] == "tool_lookup"
    assert errors[0]["source"] == "missing_tool"
    assert errors[0]["iteration"] == 2
    assert errors[0]["retryable"] is False