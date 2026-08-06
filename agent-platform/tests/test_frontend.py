from fastapi.testclient import TestClient

from api.app import create_app


def test_index_page_served():
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "Business Multi Tool Agent" in response.text
    assert "/static/app.js" in response.text


def test_static_css_served():
    client = TestClient(create_app())
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "app-shell" in response.text


def test_static_js_served():
    client = TestClient(create_app())
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "/api/v1/agent/runs" in response.text
    assert "/api/v1/agent/resume" in response.text