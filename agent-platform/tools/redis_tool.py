from typing import Any

from tools.base import BaseTool, ToolRequest, ToolResult
from tools.redis_store import RedisKVStore


class RedisKVTool(BaseTool):
    name = "redis_kv"
    description = (
        "Read or write short-lived business key-value data in Redis. "
        "Supported actions: get, set, delete, ttl."
    )

    def __init__(self, store: RedisKVStore) -> None:
        self.store = store

    def run(self, request: ToolRequest) -> ToolResult:
        action = str(request.params.get("action") or "get").lower()
        key = str(request.params.get("key") or request.session_id)

        if action == "set":
            value: Any = request.params.get("value", request.query)
            ttl_seconds = request.params.get("ttl_seconds")
            redis_key = self.store.set_json(
                key,
                value,
                ttl_seconds=int(ttl_seconds) if ttl_seconds else None,
            )
            return ToolResult(
                tool_name=self.name,
                success=True,
                content=f"Redis key saved: {redis_key}",
                metadata={"action": action, "key": redis_key},
            )

        if action == "get":
            value = self.store.get_json(key)
            return ToolResult(
                tool_name=self.name,
                success=True,
                content="Redis key loaded." if value is not None else "Redis key not found.",
                metadata={"action": action, "key": self.store.namespaced_key(key), "value": value},
            )

        if action == "delete":
            deleted = self.store.delete(key)
            return ToolResult(
                tool_name=self.name,
                success=True,
                content=f"Redis key deleted: {deleted}",
                metadata={"action": action, "key": self.store.namespaced_key(key), "deleted": deleted},
            )

        if action == "ttl":
            ttl = self.store.ttl(key)
            return ToolResult(
                tool_name=self.name,
                success=True,
                content=f"Redis key ttl: {ttl}",
                metadata={"action": action, "key": self.store.namespaced_key(key), "ttl": ttl},
            )

        raise ValueError(f"Unsupported Redis action: {action}")