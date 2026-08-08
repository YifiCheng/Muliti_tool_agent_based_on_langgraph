from fastapi import FastAPI
import json

from api.schemas import (
    AgentResumeRequest,
    AgentRunRequest,
    AgentRunResponse,
    AgentStateResponse,
    TraceListResponse,
    ReportResponse,
    RuntimeStatusResponse,  
)
from api.service import AgentService
from config.settings import load_settings
from observer.sqlite_store import SQLiteTraceStore

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    app = FastAPI(title="Business Multi Tool Agent API")
    service = AgentService()
    static_dir = Path(__file__).resolve().parents[1] / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}
    
    @app.get("/api/v1/status", response_model=RuntimeStatusResponse)
    def runtime_status() -> RuntimeStatusResponse:
        settings = load_settings()
        return RuntimeStatusResponse(
            app_name=settings.app.name,
            env=settings.app.env,
            llm_provider=settings.llm.provider,
            sql_backend=settings.sql.backend,
            redis_enabled=settings.redis.enabled,
            rag_docs_dir=settings.rag.docs_dir,
            agent_max_iterations=settings.agent.max_iterations,
        )
    
    @app.get("/api/v1/reports/{report_name}", response_model=ReportResponse)
    def get_report(report_name: str) -> ReportResponse:
        allowed_reports = {
            "qwen-provider-comparison": Path("eval/reports/qwen_provider_comparison.json"),
            "redis-cache-benchmark": Path("eval/reports/redis_cache_benchmark.json"),
            "public-docs-rag": Path("eval/reports/public_docs_rag_report.json"),
        }
        if report_name not in allowed_reports:
            return ReportResponse(
                name=report_name,
                exists=False,
                path="",
                data={"error": "unknown report"},
            )

        path = allowed_reports[report_name]
        if not path.exists():
            return ReportResponse(
                name=report_name,
                exists=False,
                path=str(path),
                data=None,
            )

        return ReportResponse(
            name=report_name,
            exists=True,
            path=str(path),
            data=json.loads(path.read_text(encoding="utf-8")),
        )

    @app.post("/api/v1/agent/runs", response_model=AgentRunResponse)
    def run_agent(request: AgentRunRequest) -> AgentRunResponse:
        return service.run(request)

    @app.post("/api/v1/agent/resume", response_model=AgentRunResponse)
    def resume_agent(request: AgentResumeRequest) -> AgentRunResponse:
        return service.resume(request)

    @app.get(
        "/api/v1/agent/runs/{thread_id}",
        response_model=AgentStateResponse,
    )
    def get_agent_state(thread_id: str) -> AgentStateResponse:
        return service.get_state(thread_id)

    @app.get("/api/v1/traces/{trace_id}", response_model=TraceListResponse)
    def get_trace(trace_id: str, limit: int = 50) -> TraceListResponse:
        settings = load_settings()
        store = SQLiteTraceStore(settings.observer.sqlite_path)
        events = [
            event.model_dump()
            for event in store.list_by_trace(trace_id, limit=limit)
        ]
        return TraceListResponse(trace_id=trace_id, events=events)

    return app


app = create_app()