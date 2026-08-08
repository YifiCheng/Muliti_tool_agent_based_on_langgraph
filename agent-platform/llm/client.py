import os
from typing import Any

from config.settings import Settings, load_settings
from llm.errors import LLMConfigError
from llm.providers.mock import MockLLMProvider
from llm.providers.openai_compatible import OpenAICompatibleProvider
from llm.providers.qwen_api import QwenAPIProvider


class LLMClient:
    def __init__(self, provider: Any) -> None:
        self.provider = provider

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        return self.provider.chat(messages, temperature=temperature)

    def chat_json(self, messages: list[dict[str, str]], schema_name: str) -> dict[str, Any]:
        return self.provider.chat_json(messages, schema_name=schema_name)


def build_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or load_settings()
    provider_name = settings.llm.provider

    if provider_name == "mock":
        print("当前是mock模式...")
        return LLMClient(MockLLMProvider())

    if provider_name == "qwen_api":
        provider_config = settings.llm.qwen_api
        return LLMClient(
            QwenAPIProvider(
                base_url=_read_env(provider_config.base_url_env),
                api_key=_read_env(provider_config.api_key_env),
                model=_read_env(provider_config.model_env),
                timeout_seconds=settings.llm.timeout_seconds,
                max_retries=settings.llm.max_retries,
                queue_wait_timeout_seconds=settings.llm.queue_wait_timeout_seconds,
                max_output_tokens=settings.llm.max_output_tokens,
            )
        )

    if provider_name == "remote_qwen":
        provider_config = settings.llm.remote_qwen
        return LLMClient(
            OpenAICompatibleProvider(
                base_url=_read_env(provider_config.base_url_env),
                api_key=_read_env(provider_config.api_key_env),
                model=_read_env(provider_config.model_env),
                timeout_seconds=settings.llm.timeout_seconds,
                max_retries=settings.llm.max_retries,
                max_output_tokens=settings.llm.max_output_tokens,
            )
        )

    raise LLMConfigError(f"Unsupported LLM provider: {provider_name}")


def _read_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise LLMConfigError(f"Missing required environment variable: {name}")
    return value