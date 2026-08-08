from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymysql

from tools.base import BaseTool, ToolRequest, ToolResult
from tools.sql_guard import validate_readonly_sql


@dataclass
class MySQLConnectionConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"
    connect_timeout_seconds: int = 5
    read_timeout_seconds: int = 10
    write_timeout_seconds: int = 10


class MySQLExecutor:
    def __init__(self, config: MySQLConnectionConfig, max_rows: int = 50) -> None:
        self.config = config
        self.max_rows = max_rows

    def execute(self, sql: str) -> list[dict[str, Any]]:
        safe_sql = validate_readonly_sql(sql)
        limited_sql = self._ensure_limit(safe_sql)

        conn = pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            charset=self.config.charset,
            connect_timeout=self.config.connect_timeout_seconds,
            read_timeout=self.config.read_timeout_seconds,
            write_timeout=self.config.write_timeout_seconds,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(limited_sql)
                rows = cursor.fetchall()
        finally:
            conn.close()

        return list(rows)

    def get_table_names(self) -> list[str]:
        sql = """
        SELECT table_name AS table_name
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY table_name
        """
        rows = self.execute(sql)
        return [str(row["table_name"]) for row in rows]

    def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        safe_table = table_name.replace("`", "")
        sql = f"""
        SELECT
            column_name,
            column_type,
            is_nullable,
            column_key,
            column_default,
            extra
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = '{safe_table}'
        ORDER BY ordinal_position
        """
        return self.execute(sql)

    def _ensure_limit(self, sql: str) -> str:
        if " limit " in f" {sql.lower()} ":
            return sql
        return f"{sql} LIMIT {self.max_rows}"


class MySQLQueryTool(BaseTool):
    name = "sql_query"
    description = "Run safe read-only SQL queries on the MySQL business database."

    def __init__(self, executor: MySQLExecutor) -> None:
        self.executor = executor

    def run(self, request: ToolRequest) -> ToolResult:
        sql = request.params.get("sql") or plan_sql_from_query(request.query)
        rows = self.executor.execute(sql)
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=f"查询到 {len(rows)} 条结构化数据。",
            metadata={
                "sql": sql,
                "rows": rows,
                "row_count": len(rows),
            },
        )


def plan_sql_from_query(query: str) -> str:
    if any(token in query for token in ["最高", "最大", "销售额最高"]):
        return """
        SELECT p.product_name, SUM(o.amount) AS total_amount
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.product_name
        ORDER BY total_amount DESC
        LIMIT 1
        """

    if "深圳" in query and "客户" in query:
        return """
        SELECT customer_name, city, industry
        FROM customers
        WHERE city = '深圳'
        ORDER BY customer_id
        """

    if any(token in query for token in ["销售部", "7月", "七月"]):
        return """
        SELECT department, SUM(amount) AS total_amount
        FROM orders
        WHERE department = '销售部'
          AND order_date >= '2026-07-01'
          AND order_date < '2026-08-01'
        GROUP BY department
        """

    return """
    SELECT order_id, order_date, amount, department
    FROM orders
    ORDER BY order_date DESC
    LIMIT 5
    """