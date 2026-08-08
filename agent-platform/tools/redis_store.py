from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import redis


@dataclass
class RedisConnectionConfig:
    host: str
    port: int
    db: int = 0
    password: str | None = None
    socket_timeout_seconds: int = 3
    key_prefix: str = "business-agent"
    default_ttl_seconds: int = 3600


class RedisKVStore:
    def __init__(
        self,
        config: RedisConnectionConfig,
        client: redis.Redis | None = None,
    ) -> None:
        self.config = config
        self.client = client or redis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            password=config.password or None,
            socket_timeout=config.socket_timeout_seconds,
            socket_connect_timeout=config.socket_timeout_seconds,
            decode_responses=True,
        )

    def ping(self) -> bool:
        return bool(self.client.ping())

    def namespaced_key(self, key: str) -> str:
        cleaned = key.strip()
        if not cleaned:
            raise ValueError("Redis key cannot be empty")
        return f"{self.config.key_prefix}:{cleaned}"

    def set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> str:
        redis_key = self.namespaced_key(key)
        ttl = ttl_seconds or self.config.default_ttl_seconds
        payload = json.dumps(value, ensure_ascii=False)
        self.client.set(redis_key, payload, ex=ttl)
        return redis_key

    def get_json(self, key: str) -> Any | None:
        redis_key = self.namespaced_key(key)
        payload = self.client.get(redis_key)
        if payload is None:
            return None
        return json.loads(payload)

    def delete(self, key: str) -> int:
        redis_key = self.namespaced_key(key)
        return int(self.client.delete(redis_key))

    def ttl(self, key: str) -> int:
        redis_key = self.namespaced_key(key)
        return int(self.client.ttl(redis_key))