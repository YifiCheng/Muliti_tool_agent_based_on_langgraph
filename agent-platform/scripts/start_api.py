import os
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from scripts.init_sqlite import init_sqlite


def main() -> None:
    settings = load_settings()
    db_path = init_sqlite()
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"app={settings.app.name}")
    print(f"provider={settings.llm.provider}")
    print(f"sqlite_db={db_path}")
    print(f"api_host={host}")
    print(f"api_port={port}")

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()