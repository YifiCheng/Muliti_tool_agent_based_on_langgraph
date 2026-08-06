import json

from fastapi.testclient import TestClient

from api.app import create_app


def main() -> None:
    client = TestClient(create_app())

    health = client.get("/health")
    print("health=", health.json())

    run = client.post(
        "/api/v1/agent/runs",
        json={
            "query": "销售额最高的商品是什么？",
            "session_id": "smoke-api-session",
            "trace_id": "smoke-api-trace",
            "thread_id": "smoke-api-thread",
            "require_sql_approval": True,
        },
    )
    print("run=", json.dumps(run.json(), ensure_ascii=False, indent=2))

    resume = client.post(
        "/api/v1/agent/resume",
        json={
            "thread_id": "smoke-api-thread",
            "decision": "approve",
            "reason": "smoke api approved",
        },
    )
    print("resume=", json.dumps(resume.json(), ensure_ascii=False, indent=2))

    trace = client.get("/api/v1/traces/smoke-api-trace")
    print("trace_event_count=", len(trace.json()["events"]))


if __name__ == "__main__":
    main()