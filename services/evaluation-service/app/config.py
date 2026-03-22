from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_EVAL_SVC_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILES = tuple(
    p for p in (_EVAL_SVC_ROOT / ".env", _REPO_ROOT / ".env") if p.is_file()
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES if _ENV_FILES else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    kafka_brokers: str = "localhost:9092"
    kafka_topic_queries: str = "queries.completed"
    kafka_consumer_group: str = "evaluation-service"

    claude_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("CLAUDE_API_KEY", "claude_api_key"),
    )
    claude_model: str = Field(
        default="claude-haiku-4-5-20251001",
        validation_alias=AliasChoices("CLAUDE_MODEL", "claude_model"),
    )
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
    )

    database_url: str = (
        "postgresql+asyncpg://pageindex:pageindex_password@localhost:5433/pageindex_eval"
    )

    evaluation_service_port: int = 8084
    evaluation_sampling_rate: float = 1.0
