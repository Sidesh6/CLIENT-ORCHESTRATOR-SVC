"""
Workflow execution and event schemas for Client Orchestrator Service.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class PipelineRunRequest(BaseModel):
    min_qualification_score: float = 75.0
    limit: int = 20
    force_resync: bool = False


class WorkflowStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_name: str
    service_target: str
    status: str
    message: Optional[str] = None
    executed_at: datetime


class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    leads_discovered_count: int
    leads_enriched_count: int
    leads_saved_count: int
    proposals_staged_count: int
    errors: list[str] = Field(default_factory=list)
    started_at: datetime
    finished_at: Optional[datetime] = None
    steps: list[WorkflowStepResponse] = Field(default_factory=list)


class PipelineRunListResponse(BaseModel):
    items: list[PipelineRunResponse]
    total: int


class DomainEventPayload(BaseModel):
    event_type: str  # 'lead.discovered', 'lead.enriched', 'proposal.approved', 'message.sent'
    source_service: str
    entity_id: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
