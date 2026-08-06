import sqlite3

import pytest

from tools.base import ToolRequest
from tools.runner import run_tool_safely
from tools.sql_guard import validate_readonly_sql
from tools.sql_tool import SQLQueryTool, SQLiteExecutor, plan_sql_from_query


def create_test_db(tmp_path):
    db_path = tmp_path / "business.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL
            );
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                department TEXT NOT NULL,
                order_date TEXT NOT NULL
            );
            INSERT INTO products VALUES
            (1, '智能客服套餐'),
            (2, '数据分析套餐');
            INSERT INTO orders VALUES
            (1, 1, 128000, '销售部', '2026-07-03'),
            (2, 2, 96000, '销售部', '2026-07-08');
            """
        )
    return db_path


def test_validate_readonly_sql_accepts_select():
    assert validate_readonly_sql("select * from orders") == "select * from orders"


def test_validate_readonly_sql_rejects_delete():
    with pytest.raises(ValueError):
        validate_readonly_sql("delete from orders")


def test_validate_readonly_sql_rejects_multi_statement():
    with pytest.raises(ValueError):
        validate_readonly_sql("select * from orders; drop table orders")


def test_sqlite_executor_returns_rows(tmp_path):
    executor = SQLiteExecutor(create_test_db(tmp_path), max_rows=10)
    rows = executor.execute("select * from orders")
    assert len(rows) == 2


def test_sqlite_executor_adds_limit(tmp_path):
    executor = SQLiteExecutor(create_test_db(tmp_path), max_rows=1)
    rows = executor.execute("select * from orders order by order_id")
    assert len(rows) == 1


def test_plan_sql_from_query_highest_sales():
    sql = plan_sql_from_query("销售额最高的商品是什么？")
    assert "ORDER BY total_amount DESC" in sql
    assert "LIMIT 1" in sql


def test_sql_query_tool(tmp_path):
    tool = SQLQueryTool(SQLiteExecutor(create_test_db(tmp_path), max_rows=10))
    result = tool.run(
        ToolRequest(query="销售额最高的商品是什么？", session_id="s1")
    )
    assert result.success is True
    assert result.metadata["row_count"] == 1
    assert result.metadata["rows"][0]["product_name"] == "智能客服套餐"


def test_sql_query_tool_wraps_invalid_sql(tmp_path):
    tool = SQLQueryTool(SQLiteExecutor(create_test_db(tmp_path), max_rows=10))
    result = run_tool_safely(
        tool,
        ToolRequest(
            query="bad",
            session_id="s1",
            params={"sql": "drop table orders"},
        ),
    )
    assert result.success is False
    assert "Only SELECT" in result.error or "Forbidden SQL" in result.error