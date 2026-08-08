import pytest

from tools.mysql_tool import MySQLConnectionConfig, MySQLExecutor


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed_sql = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        self.executed_sql = sql

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False
        self.cursor_obj = FakeCursor(rows)

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


def test_mysql_executor_adds_limit(monkeypatch):
    conn = FakeConnection([{"order_id": 1}])

    def fake_connect(**kwargs):
        return conn

    monkeypatch.setattr("tools.mysql_tool.pymysql.connect", fake_connect)

    executor = MySQLExecutor(
        MySQLConnectionConfig(
            host="localhost",
            port=3306,
            user="demo",
            password="demo",
            database="demo",
        ),
        max_rows=1,
    )

    rows = executor.execute("SELECT * FROM orders ORDER BY order_id")
    assert rows == [{"order_id": 1}]
    assert "LIMIT 1" in conn.cursor_obj.executed_sql.upper()
    assert conn.closed is True


def test_mysql_executor_rejects_write_sql():
    executor = MySQLExecutor(
        MySQLConnectionConfig(
            host="localhost",
            port=3306,
            user="demo",
            password="demo",
            database="demo",
        )
    )
    with pytest.raises(ValueError):
        executor.execute("DROP TABLE orders")