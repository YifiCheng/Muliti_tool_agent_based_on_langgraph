class ToolError(Exception):
    """Base exception for tool failures."""


class ToolNotFoundError(ToolError):
    """Raised when a tool name is not registered."""


class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""