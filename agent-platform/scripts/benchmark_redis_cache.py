import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings, load_settings
from scripts.init_sqlite import init_sqlite
from tools.mysql_tool import MySQLConnectionConfig, MySQLExecutor
from tools.redis_store import RedisConnectionConfig, RedisKVStore
from tools.sql_tool import SQLiteExecutor, plan_sql_from_query


def read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_redis_store(settings: Settings) -> RedisKVStore:
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


def build_sql_executor(settings: Settings):
    if settings.sql.backend == "mysql":
        sql_cfg = settings.sql
        return MySQLExecutor(
            MySQLConnectionConfig(
                host=read_required_env(sql_cfg.mysql_host_env),
                port=int(read_required_env(sql_cfg.mysql_port_env)),
                user=read_required_env(sql_cfg.mysql_user_env),
                password=read_required_env(sql_cfg.mysql_password_env),
                database=read_required_env(sql_cfg.mysql_database_env),
                charset=sql_cfg.mysql_charset,
                connect_timeout_seconds=sql_cfg.mysql_connect_timeout_seconds,
                read_timeout_seconds=sql_cfg.mysql_read_timeout_seconds,
                write_timeout_seconds=sql_cfg.mysql_write_timeout_seconds,
            ),
            max_rows=settings.sql.max_rows,
        )

    init_sqlite()
    return SQLiteExecutor(
        settings.sql.sqlite_path,
        max_rows=settings.sql.max_rows,
    )


def cache_key_for(query: str, sql: str) -> str:
    digest = hashlib.sha256(f"{query}\n{sql}".encode("utf-8")).hexdigest()[:16]
    return f"sql-cache:{digest}"


def execute_sql(executor, sql: str, simulate_delay_ms: int) -> list[dict[str, Any]]:
    if simulate_delay_ms > 0:
        time.sleep(simulate_delay_ms / 1000)
    return executor.execute(sql)


def timed_call(fn) -> tuple[int, Any]:
    started = perf_counter()
    value = fn()
    return int((perf_counter() - started) * 1000), value


def summarize_latency(items: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    latencies = [item["latency_ms"] for item in items if item["mode"] == mode]
    if not latencies:
        return {"count": 0, "avg_ms": None, "min_ms": None, "max_ms": None}
    return {
        "count": len(latencies),
        "avg_ms": round(mean(latencies), 2),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
    }


def print_table(results: list[dict[str, Any]]) -> None:
    print("mode\tcache_hit\tlatency_ms\trow_count")
    for item in results:
        print(
            f"{item['mode']}\t{item['cache_hit']}\t"
            f"{item['latency_ms']}\t{item['row_count']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default="销售额最高的商品是什么",
    )
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--ttl-seconds", type=int, default=300)
    parser.add_argument(
        "--simulate-delay-ms",
        type=int,
        default=0,
        help=(
            "Optional artificial delay before database reads. Use this when "
            "local SQLite/MySQL is too fast to demonstrate cache benefit."
        ),
    )
    parser.add_argument(
        "--output",
        default="eval/reports/redis_cache_benchmark.json",
    )
    args = parser.parse_args()

    if args.repeat < 1:
        raise ValueError("--repeat must be >= 1")

    settings = load_settings()
    store = build_redis_store(settings)
    executor = build_sql_executor(settings)
    if not store.ping():
        raise RuntimeError("Redis ping failed")

    sql = plan_sql_from_query(args.query)
    cache_key = cache_key_for(args.query, sql)
    store.delete(cache_key)

    results: list[dict[str, Any]] = []

    for index in range(args.repeat):
        latency_ms, rows = timed_call(
            lambda: execute_sql(executor, sql, args.simulate_delay_ms)
        )
        results.append(
            {
                "mode": "no_cache",
                "iteration": index + 1,
                "cache_hit": False,
                "latency_ms": latency_ms,
                "row_count": len(rows),
            }
        )

    latency_ms, cached = timed_call(lambda: store.get_json(cache_key))
    cache_hit = cached is not None
    if cache_hit:
        first_rows = cached["rows"]
    else:
        db_latency_ms, first_rows = timed_call(
            lambda: execute_sql(executor, sql, args.simulate_delay_ms)
        )
        store.set_json(
            cache_key,
            {"query": args.query, "sql": sql, "rows": first_rows},
            ttl_seconds=args.ttl_seconds,
        )
        latency_ms += db_latency_ms

    results.append(
        {
            "mode": "redis_first",
            "iteration": 1,
            "cache_hit": cache_hit,
            "latency_ms": latency_ms,
            "row_count": len(first_rows),
        }
    )

    for index in range(args.repeat):
        latency_ms, cached = timed_call(lambda: store.get_json(cache_key))
        if cached is None:
            raise RuntimeError("Redis cache unexpectedly missed during hit benchmark")
        results.append(
            {
                "mode": "redis_hit",
                "iteration": index + 1,
                "cache_hit": True,
                "latency_ms": latency_ms,
                "row_count": len(cached["rows"]),
            }
        )

    report = {
        "query": args.query,
        "sql": sql,
        "cache_key": store.namespaced_key(cache_key),
        "sql_backend": settings.sql.backend,
        "simulate_delay_ms": args.simulate_delay_ms,
        "summary": {
            "no_cache": summarize_latency(results, "no_cache"),
            "redis_first": summarize_latency(results, "redis_first"),
            "redis_hit": summarize_latency(results, "redis_hit"),
        },
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print_table(results)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"output={output_path}")
    print("benchmark_redis_cache=ready")


if __name__ == "__main__":
    main()
