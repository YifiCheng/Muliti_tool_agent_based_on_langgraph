import sqlite3
from pathlib import Path
from typing import Any

from tools.base import BaseTool, ToolRequest, ToolResult
from tools.sql_guard import validate_readonly_sql


class SQLiteExecutor:
    def __init__(self, db_path: str | Path, max_rows: int = 50) -> None:
        self.db_path = Path(db_path)
        self.max_rows = max_rows

    def execute(self, sql: str) -> list[dict[str, Any]]:
        safe_sql = validate_readonly_sql(sql)
        limited_sql = self._ensure_limit(safe_sql)

        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.db_path}")

        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(limited_sql).fetchall()

        return [dict(row) for row in rows]

    def _ensure_limit(self, sql: str) -> str:
        if re_search_limit(sql):
            return sql
        return f"{sql} LIMIT {self.max_rows}"


class SQLQueryTool(BaseTool):
    name = "sql_query"
    description = "Run safe read-only SQL queries on the business database."

    def __init__(self, executor: SQLiteExecutor) -> None:
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


def re_search_limit(sql: str) -> bool:
    return " limit " in f" {sql.lower()} "


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