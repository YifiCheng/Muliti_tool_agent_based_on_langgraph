from eval.metrics import contains_all_keywords, has_evidence, tool_match


def test_contains_all_keywords():
    assert contains_all_keywords("需要部门负责人和财务负责人审批", ["部门负责人", "财务负责人"])


def test_tool_match():
    assert tool_match(["document_search"], ["document_search"])
    assert not tool_match(["document_search"], ["sql_query"])


def test_has_evidence():
    assert has_evidence({"evidence": [{"source": "policy.md"}]})
    assert not has_evidence({"evidence": []})