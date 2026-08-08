import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from llm.client import build_llm_client
from tools.mysql_tool import MySQLConnectionConfig, MySQLExecutor


REQUIRED_DEMO_TABLES = {"customers", "products", "orders"}


def read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required MySQL environment variable: {name}. "
            "Set MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, "
            "and MYSQL_DATABASE in agent-platform/.env or current shell."
        )
    return value


def build_mysql_config(sql_cfg) -> MySQLConnectionConfig:
    host = read_required_env(sql_cfg.mysql_host_env)
    port_raw = read_required_env(sql_cfg.mysql_port_env)
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid MySQL port in {sql_cfg.mysql_port_env}: {port_raw}"
        ) from exc
    user = read_required_env(sql_cfg.mysql_user_env)
    password = read_required_env(sql_cfg.mysql_password_env)
    database = read_required_env(sql_cfg.mysql_database_env)

    return MySQLConnectionConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=sql_cfg.mysql_charset,
        connect_timeout_seconds=sql_cfg.mysql_connect_timeout_seconds,
        read_timeout_seconds=sql_cfg.mysql_read_timeout_seconds,
        write_timeout_seconds=sql_cfg.mysql_write_timeout_seconds,
    )


def validate_demo_schema(executor: MySQLExecutor) -> list[str]:
    tables = executor.get_table_names()
    if not tables:
        raise RuntimeError(
            "Connected to MySQL, but the selected database has no tables. "
            "This is not a read-only permission problem. Initialize demo tables "
            "with scripts/init_mysql_demo.py using a writable account, or point "
            "MYSQL_DATABASE to a database that already contains business tables."
        )

    missing = sorted(REQUIRED_DEMO_TABLES.difference(tables))
    if missing:
        raise RuntimeError(
            "Connected to MySQL, but demo table(s) are missing: "
            f"{missing}. Existing tables: {tables}. The smoke query expects "
            "customers, products, and orders."
        )
    return tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default="销售额最高的商品是什么？",
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
    )
    args = parser.parse_args()

    settings = load_settings()
    if settings.sql.backend != "mysql":
        raise RuntimeError(f"SQL backend must be mysql, got {settings.sql.backend}")

    sql_cfg = settings.sql
    executor = MySQLExecutor(
        build_mysql_config(sql_cfg),
        max_rows=sql_cfg.max_rows,
    )

    started = perf_counter()
    if args.show_schema:
        tables = executor.get_table_names()
        result = {
            "tables": tables,
            "demo_tables_ready": REQUIRED_DEMO_TABLES.issubset(tables),
        }
        if not tables:
            raise RuntimeError(
                "Connected to MySQL, but the selected database has no tables. "
                "Run scripts/init_mysql_demo.py with a writable account, or "
                "switch MYSQL_DATABASE to an existing business database."
            )
    else:
        validate_demo_schema(executor)
        client = build_llm_client(settings)
        result = {
            "answer": client.chat(
                [{"role": "user", "content": args.query}],
                temperature=0.2,
            ),
            "rows": executor.execute(
                "SELECT * FROM orders ORDER BY order_id DESC LIMIT 5"
            ),
        }
    latency_ms = int((perf_counter() - started) * 1000)

    print(f"latency_ms={latency_ms}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("smoke_mysql=ready")


if __name__ == "__main__":
    main()
