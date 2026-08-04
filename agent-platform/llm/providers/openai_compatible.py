import json
import time
from typing import Any

import httpx

from llm.errors import LLMConfigError, LLMResponseError


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
        max_retries: int = 2,
    ) -> None:
        if not base_url:
            raise LLMConfigError("LLM base_url is required")
        if not api_key:
            raise LLMConfigError("LLM api_key is required")
        if not model:
            raise LLMConfigError("LLM model is required")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        data = self._post_chat_completions(payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError(f"Invalid chat response: {data}") from exc

    def chat_json(self, messages: list[dict[str, str]], schema_name: str) -> dict[str, Any]:
        json_messages = [
            *messages,
            {
                "role": "system",
                "content": (
                    "Return only valid JSON. Do not wrap it in markdown. "
                    f"The expected schema name is: {schema_name}."
                ),
            },
        ]
        content = self.chat(json_messages, temperature=0.0)
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"LLM did not return valid JSON: {content}") from exc

    def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))

        raise LLMResponseError(f"LLM request failed after retries: {last_error}") from last_error