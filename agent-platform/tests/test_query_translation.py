from rag.query_translation import (
    NoopQueryTranslator,
    RuleBasedQueryTranslator,
    contains_cjk,
)


def test_contains_cjk() -> None:
    assert contains_cjk("如何沟通")
    assert not contains_cjk("communication")


def test_noop_translator_keeps_query() -> None:
    result = NoopQueryTranslator().translate("如何沟通")

    assert result.search_query == "如何沟通"
    assert result.translated is False
    assert result.strategy == "noop"


def test_rule_based_translates_chinese_public_doc_query() -> None:
    result = RuleBasedQueryTranslator().translate(
        "GitLab handbook 中如何描述沟通方式？"
    )

    assert result.translated is True
    assert "GitLab" in result.search_query
    assert "communication" in result.search_query
    assert "handbook" in result.search_query
    assert result.strategy == "rule_based"


def test_rule_based_keeps_english_query() -> None:
    result = RuleBasedQueryTranslator().translate(
        "What does the GitLab handbook say about communication?"
    )

    assert result.search_query == "What does the GitLab handbook say about communication?"
    assert result.translated is False
    assert result.strategy == "rule_based_no_cjk"


def test_rule_based_no_match_keeps_original_query() -> None:
    result = RuleBasedQueryTranslator().translate("这个问题没有词典匹配")

    assert result.search_query == "这个问题没有词典匹配"
    assert result.translated is False
    assert result.strategy == "rule_based_no_match"