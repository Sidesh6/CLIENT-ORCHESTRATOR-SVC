from datetime import UTC, datetime
from fastapi import APIRouter
from src.database.session import check_db_connection
from src.schemas.topology import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    db_ok = check_db_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service="client-orchestrator-svc",
        version="0.1.0",
        database="connected" if db_ok else "unreachable",
        timestamp=datetime.now(UTC),
    )
