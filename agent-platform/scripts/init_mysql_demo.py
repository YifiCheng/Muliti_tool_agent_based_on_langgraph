import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from tools.mysql_tool import MySQLConnectionConfig
import pymysql


def read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required MySQL environment variable: {name}. "
            "Set MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, "
            "and MYSQL_DATABASE before initializing MySQL demo data."
        )
    return value


def split_sql_statements(sql: str) -> list[str]:
    statements = []
    current = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    tail = "\n".join(current).strip()
    if tail:
        statements.append(tail.rstrip(";").strip())
    return statements


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schema",
        default="data/sql/schema.sql",
    )
    parser.add_argument(
        "--seed",
        default="data/sql/seed.sql",
    )
    args = parser.parse_args()

    settings = load_settings()
    if settings.sql.backend != "mysql":
        raise RuntimeError("SQL backend must be mysql for init_mysql_demo.py")

    host = read_required_env(settings.sql.mysql_host_env)
    port = int(read_required_env(settings.sql.mysql_port_env))
    user = read_required_env(settings.sql.mysql_user_env)
    password = read_required_env(settings.sql.mysql_password_env)
    database = read_required_env(settings.sql.mysql_database_env)

    cfg = MySQLConnectionConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=settings.sql.mysql_charset,
        connect_timeout_seconds=settings.sql.mysql_connect_timeout_seconds,
        read_timeout_seconds=settings.sql.mysql_read_timeout_seconds,
        write_timeout_seconds=settings.sql.mysql_write_timeout_seconds,
    )

    schema_sql = Path(args.schema).read_text(encoding="utf-8")
    seed_sql = Path(args.seed).read_text(encoding="utf-8")

    conn = pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset=cfg.charset,
        connect_timeout=cfg.connect_timeout_seconds,
        read_timeout=cfg.read_timeout_seconds,
        write_timeout=cfg.write_timeout_seconds,
        autocommit=True,
    )
    try:
        with conn.cursor() as cursor:
            for statement in split_sql_statements(schema_sql):
                cursor.execute(statement)
            for statement in split_sql_statements(seed_sql):
                cursor.execute(statement)
    finally:
        conn.close()

    print("mysql_init=ready")


if __name__ == "__main__":
    main()
