"""
SQLAlchemy models for workflow execution runs and step auditing.
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Optional
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    return str(uuid.uuid4())


class PipelineRunModel(Base):
    """Execution log for an orchestrated pipeline execution."""
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # 'running', 'completed', 'failed'
    leads_discovered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads_enriched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads_saved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    proposals_staged_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    steps: Mapped[list["WorkflowStepLogModel"]] = relationship("WorkflowStepLogModel", back_populates="run", cascade="all, delete-orphan")


class WorkflowStepLogModel(Base):
    """Step execution trace within a pipeline run."""
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    pipeline_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_target: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    run: Mapped[Optional["PipelineRunModel"]] = relationship(
        "PipelineRunModel",
        back_populates="steps",
    )
