class LLMError(Exception):
    """Base exception for LLM client failures."""


class LLMConfigError(LLMError):
    """Raised when provider config is missing or invalid."""


class LLMResponseError(LLMError):
    """Raised when provider response cannot be parsed."""