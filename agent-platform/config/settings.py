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
    backend: Literal["sqlite", "mysql"] = "sqlite"
    sqlite_path: str = "data/sql/business.db"
    mysql_host_env: str = "MYSQL_HOST"
    mysql_port_env: str = "MYSQL_PORT"
    mysql_user_env: str = "MYSQL_USER"
    mysql_password_env: str = "MYSQL_PASSWORD"
    mysql_database_env: str = "MYSQL_DATABASE"
    mysql_charset: str = "utf8mb4"
    mysql_connect_timeout_seconds: int = Field(default=5, ge=1, le=60)
    mysql_read_timeout_seconds: int = Field(default=10, ge=1, le=120)
    mysql_write_timeout_seconds: int = Field(default=10, ge=1, le=120)
    max_rows: int = 50
    timeout_seconds: int = 5

class RedisConfig(BaseModel):
    enabled: bool = False
    host_env: str = "REDIS_HOST"
    port_env: str = "REDIS_PORT"
    db_env: str = "REDIS_DB"
    password_env: str = "REDIS_PASSWORD"
    socket_timeout_seconds: int = Field(default=3, ge=1, le=30)
    key_prefix: str = "business-agent"
    default_ttl_seconds: int = Field(default=3600, ge=1, le=86400)

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
    redis: RedisConfig
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