from llm.client import build_llm_client
from llm.providers.mock import MockLLMProvider
from llm.providers.openai_compatible import OpenAICompatibleProvider
from llm.providers.qwen_api import QwenAPIProvider
from config.settings import load_settings


def test_build_mock_provider():
    settings = load_settings()
    settings.llm.provider = "mock"

    client = build_llm_client(settings)

    assert isinstance(client.provider, MockLLMProvider)


def test_build_qwen_api_provider_without_network(monkeypatch):
    monkeypatch.setenv("QWEN_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.setenv("QWEN_MODEL", "qwen-test")

    settings = load_settings()
    settings.llm.provider = "qwen_api"
    client = build_llm_client(settings)

    assert isinstance(client.provider, QwenAPIProvider)
    assert client.provider.model == "qwen-test"


def test_build_remote_qwen_provider_without_network(monkeypatch):
    monkeypatch.setenv("REMOTE_QWEN_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("REMOTE_QWEN_API_KEY", "test-key")
    monkeypatch.setenv("REMOTE_QWEN_MODEL", "remote-qwen")

    settings = load_settings()
    settings.llm.provider = "remote_qwen"
    client = build_llm_client(settings)

    assert isinstance(client.provider, OpenAICompatibleProvider)
    assert client.provider.model == "remote-qwen"