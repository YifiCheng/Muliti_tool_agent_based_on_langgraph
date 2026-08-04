import pytest

from llm.client import LLMClient, build_llm_client
from llm.errors import LLMConfigError
from llm.providers.mock import MockLLMProvider


def test_mock_chat():
    client = LLMClient(MockLLMProvider())
    result = client.chat([{"role": "user", "content": "hello"}])
    assert result == "mock response: hello"


def test_mock_chat_json_plan():
    client = LLMClient(MockLLMProvider())
    result = client.chat_json(
        [{"role": "user", "content": "plan this task"}],
        schema_name="plan",
    )
    assert result["tools"] == ["mock_search"]


def test_build_default_mock_client():
    client = build_llm_client()
    result = client.chat([{"role": "user", "content": "hello"}])
    assert result.startswith("mock response")