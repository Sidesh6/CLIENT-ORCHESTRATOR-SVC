from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Client Orchestrator Service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development")
    app_debug: bool = Field(default=False)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8004)

    database_url: str = Field(default="sqlite:///./data/orchestrator.db")

    # Platform service URLs
    finder_svc_url: str = Field(default="http://localhost:8000")
    messager_svc_url: str = Field(default="http://localhost:8001")
    intelligence_svc_url: str = Field(default="http://localhost:8002")
    core_svc_url: str = Field(default="http://localhost:8003")

    pipeline_min_qualification_score: float = 75.0
    pipeline_sync_interval_minutes: int = 15

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def data_dir(self) -> Path:
        d = self.base_dir / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d


settings = Settings()
