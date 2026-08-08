from eval.metrics import (
    contains_all_keywords,
    evidence_count_at_least,
    evidence_source_match,
    has_evidence,
    tool_match,
)


def test_contains_all_keywords():
    assert contains_all_keywords("需要部门负责人和财务负责人审批", ["部门负责人", "财务负责人"])


def test_tool_match():
    assert tool_match(["document_search"], ["document_search"])
    assert not tool_match(["document_search"], ["sql_query"])


def test_has_evidence():
    assert has_evidence({"evidence": [{"source": "policy.md"}]})
    assert not has_evidence({"evidence": []})

def test_evidence_count_at_least():
    state = {"evidence": [{"source": "a.md"}, {"source": "b.md"}]}

    assert evidence_count_at_least(state, 2)
    assert not evidence_count_at_least(state, 3)


def test_evidence_source_match():
    state = {"evidence": [{"source": "gitlab_handbook_values.md#0"}]}

    assert evidence_source_match(state, ["gitlab_handbook_values.md"])
    assert not evidence_source_match(state, ["clef_handbook.md"])