import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from scripts.init_sqlite import init_sqlite
from tools.base import ToolRequest
from tools.sql_tool import SQLiteExecutor, SQLQueryTool


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="销售额最高的商品是什么？")
    parser.add_argument("--sql", default="")
    args = parser.parse_args()

    settings = load_settings()
    init_sqlite()
    tool = SQLQueryTool(
        SQLiteExecutor(settings.sql.sqlite_path, max_rows=settings.sql.max_rows)
    )
    result = tool.run(
        ToolRequest(
            query=args.query,
            session_id="sql-smoke-session",
            params={"sql": args.sql} if args.sql else {},
        )
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()