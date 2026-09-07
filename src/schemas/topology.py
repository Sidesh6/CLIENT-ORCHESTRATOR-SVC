from datetime import UTC, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "client-orchestrator-svc"
    version: str = "0.1.0"
    database: str = "connected"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceStatus(BaseModel):
    name: str
    url: str
    status: str  # 'online', 'offline', 'degraded'
    latency_ms: Optional[float] = None
    last_checked: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlatformTopologyResponse(BaseModel):
    platform_name: str = "Client AI Platform"
    total_services: int = 5
    online_count: int = 0
    services: list[ServiceStatus] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
