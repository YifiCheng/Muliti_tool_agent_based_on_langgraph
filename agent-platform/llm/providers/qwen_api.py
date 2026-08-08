from llm.providers.openai_compatible import OpenAICompatibleProvider


class QwenAPIProvider(OpenAICompatibleProvider):
    name = "qwen_api"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        max_retries: int,
        queue_wait_timeout_seconds: int,
        max_output_tokens: int,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_output_tokens=max_output_tokens,
            extra_headers={
                "X-DashScope-Wait-Timeout": str(queue_wait_timeout_seconds),
            },
        )