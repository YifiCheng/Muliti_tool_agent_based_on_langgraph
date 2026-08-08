from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")


@dataclass(frozen=True)
class QueryTranslation:
    original_query: str
    search_query: str
    translated: bool
    strategy: str


class QueryTranslator(Protocol):
    def translate(self, query: str) -> QueryTranslation:
        ...


def contains_cjk(text: str) -> bool:
    return bool(_CJK_PATTERN.search(text))


class NoopQueryTranslator:
    def translate(self, query: str) -> QueryTranslation:
        return QueryTranslation(
            original_query=query,
            search_query=query,
            translated=False,
            strategy="noop",
        )


class RuleBasedQueryTranslator:
    """Small deterministic translator for public handbook retrieval demos."""

    PHRASE_MAP = {
        "沟通": "communication",
        "沟通方式": "communication",
        "异步": "async communication",
        "远程": "remote work",
        "远程办公": "remote work",
        "价值观": "values",
        "公司价值观": "company values",
        "工程": "engineering",
        "研发": "engineering",
        "产品": "product",
        "产品管理": "product management",
        "人员": "people",
        "员工": "employees",
        "员工手册": "employee handbook",
        "入职": "onboarding",
        "流程": "process",
        "计划": "planning",
        "Mattermost": "Mattermost",
        "GitLab": "GitLab",
        "Clef": "Clef",
        "handbook": "handbook",
    }

    def translate(self, query: str) -> QueryTranslation:
        query = query.strip()
        if not query:
            return QueryTranslation(
                original_query=query,
                search_query=query,
                translated=False,
                strategy="rule_based_empty",
            )

        if not contains_cjk(query):
            return QueryTranslation(
                original_query=query,
                search_query=query,
                translated=False,
                strategy="rule_based_no_cjk",
            )

        terms: list[str] = []
        for phrase, english in self.PHRASE_MAP.items():
            if phrase in query and english not in terms:
                terms.append(english)

        if not terms:
            return QueryTranslation(
                original_query=query,
                search_query=query,
                translated=False,
                strategy="rule_based_no_match",
            )

        if "handbook" not in terms:
            terms.append("handbook")

        return QueryTranslation(
            original_query=query,
            search_query=" ".join(terms),
            translated=True,
            strategy="rule_based",
        )