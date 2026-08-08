import json
import random
import re
import time
from typing import Any

import httpx

from llm.errors import LLMConfigError, LLMResponseError


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 60,
        max_retries: int = 1,
        max_output_tokens: int = 512,
        extra_headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
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
        self.max_output_tokens = max_output_tokens
        self.extra_headers = extra_headers or {}
        self.transport = transport

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        data = self._post_chat_completions(
            {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": self.max_output_tokens,
            }
        )
        return self._extract_content(data)

    def chat_json(
        self,
        messages: list[dict[str, str]],
        schema_name: str,
    ) -> dict[str, Any]:
        data = self._post_chat_completions(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return one valid JSON object only. "
                            "Do not use markdown fences. "
                            f"The schema name is {schema_name}."
                        ),
                    },
                    *messages,
                ],
                "temperature": 0,
                "max_tokens": self.max_output_tokens,
                "response_format": {"type": "json_object"},
            }
        )
        return self._parse_json(self._extract_content(data))

    def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        timeout = httpx.Timeout(
            timeout=self.timeout_seconds,
            connect=min(10, self.timeout_seconds),
            read=self.timeout_seconds,
            write=min(30, self.timeout_seconds),
            pool=min(10, self.timeout_seconds),
        )

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(
                    timeout=timeout,
                    transport=self.transport,
                ) as client:
                    response = client.post(url, headers=headers, json=payload)

                if response.status_code in RETRYABLE_STATUS_CODES:
                    raise httpx.HTTPStatusError(
                        f"Retryable HTTP status {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                if not self._should_retry(exc) or attempt >= self.max_retries:
                    break
                delay = min(4.0, 0.5 * (2**attempt)) + random.uniform(0, 0.2)
                time.sleep(delay)

        raise LLMResponseError(
            f"LLM request failed after retries: {self._error_summary(last_error)}"
        ) from last_error

    @staticmethod
    def _should_retry(exc: Exception) -> bool:
        if isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ),
        ):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in RETRYABLE_STATUS_CODES
        return False

    @staticmethod
    def _error_summary(exc: Exception | None) -> str:
        if exc is None:
            return "unknown error"
        if isinstance(exc, httpx.HTTPStatusError):
            body = exc.response.text[:500]
            return f"status={exc.response.status_code}, body={body}"
        return str(exc)

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError(f"Invalid chat response: {data}") from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError(f"Empty chat response: {data}")
        return content.strip()

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        stripped = content.strip()
        candidates = [stripped]

        fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.DOTALL)
        if fenced:
            candidates.append(fenced.group(1).strip())

        object_match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if object_match:
            candidates.append(object_match.group(0))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise LLMResponseError(f"LLM did not return valid JSON: {content[:500]}")