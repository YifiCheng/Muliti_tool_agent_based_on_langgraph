import os

from config.settings import Settings
from rag.build_index import build_retriever
from rag.query_translation import NoopQueryTranslator, RuleBasedQueryTranslator
from tools.document_search import DocumentSearchTool
from tools.mock_tools import MockCalculatorTool
from tools.registry import ToolRegistry
from tools.sql_tool import SQLiteExecutor, SQLQueryTool

from tools.mysql_tool import MySQLConnectionConfig, MySQLExecutor

from tools.redis_store import RedisConnectionConfig, RedisKVStore
from tools.redis_tool import RedisKVTool


def _read_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "MySQL backend requires MYSQL_HOST, MYSQL_PORT, MYSQL_USER, "
            "MYSQL_PASSWORD, and MYSQL_DATABASE."
        )
    return value


def _read_int_env(name: str) -> int:
    value = _read_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer environment variable {name}: {value}") from exc


def build_query_translator(settings: Settings):
    if not settings.rag.enable_query_translation:
        return NoopQueryTranslator()

    if settings.rag.query_translation_strategy == "rule_based":
        return RuleBasedQueryTranslator()

    return NoopQueryTranslator()


def build_agent_registry(settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        DocumentSearchTool(
            build_retriever(settings),
            translator=build_query_translator(settings),
        )
    )
    if settings.sql.backend == "mysql":
        registry.register(
            SQLQueryTool(
                MySQLExecutor(
                    MySQLConnectionConfig(
                        host=_read_env(settings.sql.mysql_host_env),
                        port=_read_int_env(settings.sql.mysql_port_env),
                        user=_read_env(settings.sql.mysql_user_env),
                        password=_read_env(settings.sql.mysql_password_env),
                        database=_read_env(settings.sql.mysql_database_env),
                        charset=settings.sql.mysql_charset,
                        connect_timeout_seconds=settings.sql.mysql_connect_timeout_seconds,
                        read_timeout_seconds=settings.sql.mysql_read_timeout_seconds,
                        write_timeout_seconds=settings.sql.mysql_write_timeout_seconds,
                    ),
                    max_rows=settings.sql.max_rows,
                )
            )
        )
    else:
        registry.register(
            SQLQueryTool(
                SQLiteExecutor(
                    settings.sql.sqlite_path,
                    max_rows=settings.sql.max_rows,
                )
            )
        )
    if settings.redis.enabled:
        registry.register(RedisKVTool(build_redis_store(settings)))
    registry.register(MockCalculatorTool())
    return registry


def _read_optional_env(name: str) -> str:
    return os.getenv(name, "").strip()

def build_redis_store(settings: Settings) -> RedisKVStore:
    port_raw = _read_env(settings.redis.port_env)
    db_raw = _read_env(settings.redis.db_env)
    try:
        port = int(port_raw)
        db = int(db_raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid Redis port/db: port={port_raw}, db={db_raw}"
        ) from exc

    return RedisKVStore(
        RedisConnectionConfig(
            host=_read_env(settings.redis.host_env),
            port=port,
            db=db,
            password=_read_optional_env(settings.redis.password_env) or None,
            socket_timeout_seconds=settings.redis.socket_timeout_seconds,
            key_prefix=settings.redis.key_prefix,
            default_ttl_seconds=settings.redis.default_ttl_seconds,
        )
    )