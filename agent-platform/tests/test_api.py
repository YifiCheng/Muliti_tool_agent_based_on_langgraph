from fastapi.testclient import TestClient

from api.app import create_app


def test_health():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_agent_rag_flow():
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/agent/runs",
        json={
            "query": "报销超过 5000 元需要谁审批？",
            "session_id": "api-rag-session",
            "trace_id": "api-rag-trace",
            "thread_id": "api-rag-thread",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["final_answer"]
    assert data["thread_id"] == "api-rag-thread"


def test_run_agent_can_interrupt_and_resume_sql():
    client = TestClient(create_app())
    run_response = client.post(
        "/api/v1/agent/runs",
        json={
            "query": "销售额最高的商品是什么？",
            "session_id": "api-approval-session",
            "trace_id": "api-approval-trace",
            "thread_id": "api-approval-thread",
            "require_sql_approval": True,
        },
    )

    assert run_response.status_code == 200
    run_data = run_response.json()
    assert run_data["status"] == "interrupted"
    assert run_data["interrupt"]

    resume_response = client.post(
        "/api/v1/agent/resume",
        json={
            "thread_id": "api-approval-thread",
            "decision": "approve",
            "reason": "api test approved",
        },
    )

    assert resume_response.status_code == 200
    resume_data = resume_response.json()
    assert resume_data["status"] == "completed"
    assert resume_data["approval_status"] == "approved"
    assert resume_data["final_answer"]


def test_get_agent_state():
    client = TestClient(create_app())
    client.post(
        "/api/v1/agent/runs",
        json={
            "query": "报销审批规则",
            "session_id": "api-state-session",
            "trace_id": "api-state-trace",
            "thread_id": "api-state-thread",
        },
    )

    response = client.get("/api/v1/agent/runs/api-state-thread")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["state"]["session_id"] == "api-state-session"


def test_get_trace():
    client = TestClient(create_app())
    client.post(
        "/api/v1/agent/runs",
        json={
            "query": "报销审批规则",
            "session_id": "api-trace-session",
            "trace_id": "api-trace",
            "thread_id": "api-trace-thread",
        },
    )

    response = client.get("/api/v1/traces/api-trace")
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == "api-trace"
    assert data["events"]