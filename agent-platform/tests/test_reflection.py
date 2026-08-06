from llm.client import LLMClient
from llm.providers.mock import MockLLMProvider
from reflection.llm_reflector import HybridReflector, LLMReflector
from reflection.models import ReflectionDecision
from reflection.rule_reflector import RuleReflector


def test_reflection_decision_rejects_inconsistent_action():
    try:
        ReflectionDecision(
            is_sufficient=False,
            next_action="answer",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid reflection decision was accepted")


def test_rule_reflector_retrieves_when_no_tool_result():
    decision = RuleReflector().reflect(
        query="报销审批规则",
        tool_results=[],
        evidence=[],
    )

    assert decision.is_sufficient is False
    assert decision.next_action == "retrieve_more"
    assert decision.source == "rule"


def test_rule_reflector_retrieves_when_document_has_no_evidence():
    decision = RuleReflector().reflect(
        query="报销审批规则",
        tool_results=[
            {
                "tool_name": "document_search",
                "success": True,
                "metadata": {},
            }
        ],
        evidence=[],
    )

    assert decision.next_action == "retrieve_more"
    assert "document evidence" in decision.missing_info


def test_rule_reflector_retrieves_when_sql_has_no_rows():
    decision = RuleReflector().reflect(
        query="销售额最高的商品是什么？",
        tool_results=[
            {
                "tool_name": "sql_query",
                "success": True,
                "metadata": {"rows": [], "row_count": 0},
            }
        ],
        evidence=[],
    )

    assert decision.next_action == "retrieve_more"
    assert "SQL query rows" in decision.missing_info


def test_rule_reflector_accepts_sql_rows():
    decision = RuleReflector().reflect(
        query="销售额最高的商品是什么？",
        tool_results=[
            {
                "tool_name": "sql_query",
                "success": True,
                "metadata": {
                    "rows": [{"product_name": "智能客服套餐"}],
                    "row_count": 1,
                },
            }
        ],
        evidence=[],
    )

    assert decision.is_sufficient is True
    assert decision.next_action == "answer"


def test_llm_reflector_validates_json_output():
    reflector = LLMReflector(LLMClient(MockLLMProvider()))
    decision = reflector.reflect(
        query="报销审批规则",
        tool_results=[
            {
                "tool_name": "mock_document_search",
                "success": True,
            }
        ],
        evidence=[
            {
                "source": "policy.md",
                "content": "超过 5000 元需要审批",
            }
        ],
    )

    assert decision.source == "llm"
    assert decision.is_sufficient is True


def test_hybrid_reflector_uses_rule_result_for_missing_evidence():
    reflector = HybridReflector(LLMClient(MockLLMProvider()))
    decision = reflector.reflect(
        query="报销审批规则",
        tool_results=[
            {
                "tool_name": "document_search",
                "success": True,
            }
        ],
        evidence=[],
    )

    assert decision.source == "rule"
    assert decision.next_action == "retrieve_more"