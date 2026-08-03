# 代码创建时间：2026-08-03 22:51
# 实现目标：

# - 默认读取 `config/config.yaml`；
# - 支持 `.env`；
# - 将 YAML 转成 Pydantic model；
# - 暴露 `load_settings()` 函数；
# - 路径不存在时抛出清晰错误。


from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class LLMProviderConfig(BaseModel):
    base_url_env: str
    api_key_env: str
    model_env: str


class LLMConfig(BaseModel):
    provider: Literal["mock", "qwen_api", "remote_qwen"] = "mock"
    timeout_seconds: int = 30
    max_retries: int = 2
    qwen_api: LLMProviderConfig
    remote_qwen: LLMProviderConfig


class RAGConfig(BaseModel):
    docs_dir: str
    index_dir: str
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 5


class SQLConfig(BaseModel):
    sqlite_path: str
    max_rows: int = 50
    timeout_seconds: int = 5


class ObserverConfig(BaseModel):
    sqlite_path: str


class AgentConfig(BaseModel):
    max_iterations: int = Field(default=3, ge=1, le=10)
    enable_reflection: bool = True


class AppConfig(BaseModel):
    name: str
    env: str = "dev"


class Settings(BaseModel):
    app: AppConfig
    llm: LLMConfig
    rag: RAGConfig
    sql: SQLConfig
    observer: ObserverConfig
    agent: AgentConfig


def load_settings(config_path: str | Path = "config/config.yaml") -> Settings:
    load_dotenv()
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Settings.model_validate(raw)