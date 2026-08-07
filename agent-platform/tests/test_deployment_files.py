from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "agent-platform"


def test_docker_files_exist() -> None:
    assert (APP_ROOT / "Dockerfile").exists()
    assert (APP_ROOT / ".dockerignore").exists()
    assert (APP_ROOT / "scripts" / "docker_entrypoint.py").exists()
    assert (ROOT / "docker-compose.yml").exists()
    assert (ROOT / "docs" / "deployment.md").exists()


def test_dockerfile_runs_entrypoint() -> None:
    text = (APP_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in text
    assert "EXPOSE 8000" in text
    assert 'CMD ["python", "scripts/docker_entrypoint.py"]' in text


def test_compose_maps_port_and_data_volume() -> None:
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "8000:8000" in text
    assert "./agent-platform/data:/app/data" in text
    assert "QWEN_API_KEY" in text
    assert "REMOTE_QWEN_BASE_URL" in text


def test_entrypoint_initializes_sqlite_and_uvicorn() -> None:
    text = (APP_ROOT / "scripts" / "docker_entrypoint.py").read_text(
        encoding="utf-8"
    )

    assert "init_sqlite()" in text
    assert "uvicorn.run" in text
    assert "0.0.0.0" in text


def test_dockerignore_excludes_runtime_artifacts() -> None:
    text = (APP_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert ".env" in text
    assert ".venv" in text
    assert "data/sql/*.db" in text
    assert "data/traces/*.db" in text
    assert "data/checkpoints/*.sqlite" in text