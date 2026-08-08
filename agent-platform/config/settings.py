# 代码创建时间：2026-08-03 22:51
# 实现目标：

# - 默认读取 `config/config.yaml`；
# - 支持 `.env`；
# - 将 YAML 转成 Pydantic model；
# - 暴露 `load_settings()` 函数；
# - 路径不存在时抛出清晰错误。
import os

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
    provider: Literal["mock", "qwen_api", "remote_qwen"] = "qwen_api"
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    max_retries: int = Field(default=1, ge=0, le=5)
    queue_wait_timeout_seconds: int = Field(default=10, ge=0, le=120)
    max_output_tokens: int = Field(default=512, ge=64, le=4096)
    qwen_api: LLMProviderConfig
    remote_qwen: LLMProviderConfig


class RAGConfig(BaseModel):
    docs_dir: str
    index_dir: str
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 5
    enable_query_translation: bool = True
    query_translation_strategy: Literal["noop", "rule_based"] = "rule_based"


class SQLConfig(BaseModel):
    sqlite_path: str
    max_rows: int = 50
    timeout_seconds: int = 5


class ObserverConfig(BaseModel):
    sqlite_path: str
    

class AgentConfig(BaseModel):
    max_iterations: int = Field(default=3, ge=1, le=10)
    enable_reflection: bool = True
    checkpoint_path: str = "data/checkpoints/agent_checkpoints.sqlite"
    require_sql_approval: bool = False


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


def load_settings(config_path: str | Path | None = None) -> Settings:
    load_dotenv()
    resolved_path = config_path or os.getenv(
        "AGENT_CONFIG_PATH",
        "config/config.yaml",
    )
    path = Path(resolved_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Settings.model_validate(raw)