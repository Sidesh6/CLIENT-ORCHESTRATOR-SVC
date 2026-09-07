"""
Workflow and event endpoints for Client Orchestrator Service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from src.database.session import get_db
from src.events.bus import GLOBAL_BUS
from src.schemas.topology import PlatformTopologyResponse
from src.schemas.workflow import (
    DomainEventPayload,
    PipelineRunListResponse,
    PipelineRunRequest,
    PipelineRunResponse,
)
from src.services.service_registry import GLOBAL_REGISTRY
from src.workflows.models import PipelineRunModel
from src.workflows.pipeline_runner import PipelineRunner

workflow_router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])
events_router = APIRouter(prefix="/api/v1/events", tags=["Events"])
topology_router = APIRouter(prefix="/api/v1", tags=["Topology"])


@workflow_router.post("/run-pipeline", response_model=PipelineRunResponse)
def run_pipeline(
    payload: PipelineRunRequest = PipelineRunRequest(),
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    """Trigger the end-to-end multi-service pipeline run."""
    runner = PipelineRunner(db)
    return runner.run_pipeline(payload)


@workflow_router.get("/runs", response_model=PipelineRunListResponse)
def list_pipeline_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PipelineRunListResponse:
    """List historical pipeline execution runs."""
    stmt = (
        select(PipelineRunModel)
        .options(selectinload(PipelineRunModel.steps))
        .order_by(PipelineRunModel.started_at.desc())
        .limit(limit)
    )
    runs = list(db.execute(stmt).scalars().all())
    return PipelineRunListResponse(
        items=[PipelineRunResponse.model_validate(r) for r in runs],
        total=len(runs),
    )


@workflow_router.get("/runs/{run_id}", response_model=PipelineRunResponse)
def get_pipeline_run(run_id: str, db: Session = Depends(get_db)) -> PipelineRunResponse:
    """Get step-by-step trace of a specific pipeline execution run."""
    stmt = (
        select(PipelineRunModel)
        .options(selectinload(PipelineRunModel.steps))
        .where(PipelineRunModel.id == run_id)
    )
    run = db.execute(stmt).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    return PipelineRunResponse.model_validate(run)


@events_router.post("/emit", status_code=status.HTTP_200_OK)
def emit_event(event: DomainEventPayload) -> dict[str, str]:
    """Publish a domain event across the platform."""
    GLOBAL_BUS.publish(event)
    return {"status": "published", "event_type": event.event_type}


@topology_router.get("/topology", response_model=PlatformTopologyResponse)
def get_topology() -> PlatformTopologyResponse:
    """Returns connectivity and latency status across all 5 platform services."""
    return GLOBAL_REGISTRY.get_topology()
