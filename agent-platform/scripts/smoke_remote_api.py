import argparse
import sys
from uuid import uuid4

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:18000",
    )
    parser.add_argument(
        "--query",
        default="报销超过 5000 元需要谁审批？",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    with httpx.Client(timeout=30) as client:
        health = client.get(f"{base_url}/health")
        health.raise_for_status()
        print(f"health={health.json()}")

        run_id = uuid4().hex[:8]
        payload = {
            "query": args.query,
            "session_id": f"remote-smoke-session-{run_id}",
            "trace_id": f"remote-smoke-trace-{run_id}",
            "thread_id": f"remote-smoke-thread-{run_id}",
            "require_sql_approval": False,
        }
        response = client.post(
            f"{base_url}/api/v1/agent/runs",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    print(f"status={data['status']}")
    print(f"selected_tools={data['selected_tools']}")
    print(f"trace_id={data['trace_id']}")

    if data["status"] != "completed":
        raise RuntimeError(f"unexpected status: {data['status']}")
    if not data["selected_tools"]:
        raise RuntimeError("remote API returned no selected tools")

    print("smoke_remote_api=ready")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"smoke_remote_api=failed: {exc}", file=sys.stderr)
        raise