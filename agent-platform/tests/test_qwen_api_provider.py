import json

import httpx

from llm.providers.openai_compatible import OpenAICompatibleProvider
from llm.providers.qwen_api import QwenAPIProvider


def test_qwen_provider_adds_wait_timeout_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-DashScope-Wait-Timeout"] == "10"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hello"}}]},
        )

    provider = QwenAPIProvider(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="qwen-plus",
        timeout_seconds=30,
        max_retries=0,
        queue_wait_timeout_seconds=10,
        max_output_tokens=128,
    )
    provider.transport = httpx.MockTransport(handler)

    assert provider.chat([{"role": "user", "content": "hi"}]) == "hello"


def test_chat_json_uses_json_mode_and_parses_fenced_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["max_tokens"] == 128
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "```json\n{\"tools\":[\"document_search\"]}\n```"
                        }
                    }
                ]
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="test-model",
        timeout_seconds=30,
        max_retries=0,
        max_output_tokens=128,
        transport=httpx.MockTransport(handler),
    )

    result = provider.chat_json(
        [{"role": "user", "content": "return plan"}],
        schema_name="plan",
    )

    assert result["tools"] == ["document_search"]


def test_non_retryable_401_is_not_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, json={"error": "invalid key"})

    provider = OpenAICompatibleProvider(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="test-model",
        timeout_seconds=30,
        max_retries=2,
        max_output_tokens=128,
        transport=httpx.MockTransport(handler),
    )

    try:
        provider.chat([{"role": "user", "content": "hi"}])
    except Exception as exc:
        assert "status=401" in str(exc)
    else:
        raise AssertionError("expected provider error")

    assert calls == 1