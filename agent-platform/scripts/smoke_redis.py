import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from tools.base import ToolRequest
from tools.redis_store import RedisConnectionConfig, RedisKVStore
from tools.redis_tool import RedisKVTool


def read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required Redis environment variable: {name}")
    return value


def build_store() -> RedisKVStore:
    settings = load_settings()
    redis_cfg = settings.redis
    return RedisKVStore(
        RedisConnectionConfig(
            host=read_required_env(redis_cfg.host_env),
            port=int(read_required_env(redis_cfg.port_env)),
            db=int(read_required_env(redis_cfg.db_env)),
            password=os.getenv(redis_cfg.password_env, "").strip() or None,
            socket_timeout_seconds=redis_cfg.socket_timeout_seconds,
            key_prefix=redis_cfg.key_prefix,
            default_ttl_seconds=redis_cfg.default_ttl_seconds,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default="")
    parser.add_argument("--value", default="Redis smoke value")
    args = parser.parse_args()

    store = build_store()
    tool = RedisKVTool(store)
    key = args.key or f"smoke:{uuid4().hex[:8]}"

    started = perf_counter()
    ping = store.ping()
    set_result = tool.run(
        ToolRequest(
            query=args.value,
            session_id="redis-smoke",
            params={
                "action": "set",
                "key": key,
                "value": {"message": args.value},
                "ttl_seconds": 60,
            },
        )
    )
    get_result = tool.run(
        ToolRequest(
            query="",
            session_id="redis-smoke",
            params={"action": "get", "key": key},
        )
    )
    ttl_result = tool.run(
        ToolRequest(
            query="",
            session_id="redis-smoke",
            params={"action": "ttl", "key": key},
        )
    )
    delete_result = tool.run(
        ToolRequest(
            query="",
            session_id="redis-smoke",
            params={"action": "delete", "key": key},
        )
    )
    latency_ms = int((perf_counter() - started) * 1000)

    report = {
        "ping": ping,
        "latency_ms": latency_ms,
        "set": set_result.model_dump(),
        "get": get_result.model_dump(),
        "ttl": ttl_result.model_dump(),
        "delete": delete_result.model_dump(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not ping or not set_result.success or not get_result.success:
        raise SystemExit(1)

    print("smoke_redis=ready")


if __name__ == "__main__":
    main()