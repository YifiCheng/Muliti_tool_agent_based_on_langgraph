import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings


def init_sqlite() -> Path:
    settings = load_settings()
    db_path = Path(settings.sql.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path("data/sql/schema.sql")
    seed_path = Path("data/sql/seed.sql")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.executescript(seed_path.read_text(encoding="utf-8"))

    return db_path


def main() -> None:
    db_path = init_sqlite()
    print(f"sqlite_db={db_path}")
    print("sqlite_init=ready")


if __name__ == "__main__":
    main()