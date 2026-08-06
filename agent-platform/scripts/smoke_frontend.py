import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from api.app import create_app


def main() -> None:
    client = TestClient(create_app())

    index = client.get("/")
    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")

    print("index_status=", index.status_code)
    print("css_status=", css.status_code)
    print("js_status=", js.status_code)
    print("has_title=", "Business Multi Tool Agent" in index.text)
    print("has_run_api=", "/api/v1/agent/runs" in js.text)


if __name__ == "__main__":
    main()
