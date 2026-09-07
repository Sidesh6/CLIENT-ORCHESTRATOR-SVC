"""
End-to-End Multi-Service Pipeline Runner.
Coordinates Client Finder -> Client Intelligence -> Client Core -> Client Messager.
"""

from datetime import UTC, datetime
from typing import Any, Optional
import httpx
from sqlalchemy.orm import Session
from src.config.settings import settings
from src.schemas.workflow import PipelineRunRequest, PipelineRunResponse, WorkflowStepResponse
from src.workflows.models import PipelineRunModel, WorkflowStepLogModel


class PipelineRunner:
    """Orchestrates the entire client acquisition workflow."""

    def __init__(self, session: Session, timeout: float = 10.0) -> None:
        self.session = session
        self.timeout = timeout
        self.finder_url = settings.finder_svc_url.rstrip("/")
        self.intelligence_url = settings.intelligence_svc_url.rstrip("/")
        self.core_url = settings.core_svc_url.rstrip("/")
        self.messager_url = settings.messager_svc_url.rstrip("/")

    def run_pipeline(self, req: PipelineRunRequest) -> PipelineRunResponse:
        run = PipelineRunModel(status="running")
        self.session.add(run)
        self.session.flush()

        step_logs: list[WorkflowStepLogModel] = []
        errors: list[str] = []

        discovered_count = 0
        enriched_count = 0
        saved_count = 0
        proposals_staged = 0

        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Step 1: Query Client Finder (Port 8000)
                finder_resp = client.get(
                    f"{self.finder_url}/api/projects",
                    params={"limit": req.limit},
                )
                raw_leads = []
                if finder_resp.status_code == 200:
                    data = finder_resp.json()
                    raw_leads = data.get("items", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    discovered_count = len(raw_leads)
                    self._log_step(run.id, "Fetch Leads", "client-finder-svc", "success", f"Discovered {len(raw_leads)} opportunities", step_logs)
                else:
                    self._log_step(run.id, "Fetch Leads", "client-finder-svc", "warning", f"Finder returned {finder_resp.status_code}", step_logs)

                # Process each lead through the downstream pipeline
                for item in raw_leads:
                    try:
                        title = item.get("title", "Untitled")
                        desc = item.get("description", "")
                        source = item.get("source", "Web")
                        source_url = item.get("source_url", "")
                        budget = item.get("budget")
                        skills = item.get("skills") or []

                        # Step 2: Call Client Intelligence (Port 8002)
                        intel_res = client.post(
                            f"{self.intelligence_url}/api/v1/analyze/project",
                            json={
                                "title": title,
                                "description": desc,
                                "source": source,
                                "source_url": source_url,
                                "budget": budget,
                                "skills": skills,
                            },
                        )
                        intel_data = intel_res.json() if intel_res.status_code == 200 else {}
                        if intel_data:
                            enriched_count += 1

                        score_info = intel_data.get("scoring", {}).get("score", {})
                        intel_score = score_info.get("overall_score", 0.0)

                        # Step 3: Save to Client Core CRM (Port 8003)
                        core_res = client.post(
                            f"{self.core_url}/api/v1/leads",
                            json={
                                "title": title,
                                "description": desc,
                                "source": source,
                                "source_url": str(source_url),
                                "budget": budget,
                                "skills": skills,
                                "finder_score": item.get("score"),
                                "intelligence_score": intel_score,
                                "status": "qualified" if intel_score >= req.min_qualification_score else "discovered",
                            },
                        )
                        if core_res.status_code in (200, 201):
                            saved_count += 1

                        # Step 4: If qualified (Score >= Threshold), forward to Client Messager (Port 8001)
                        if intel_score >= req.min_qualification_score:
                            messager_res = client.post(
                                f"{self.messager_url}/api/v1/ingest/project",
                                json={
                                    "external_id": str(item.get("id") or ""),
                                    "title": title,
                                    "description": desc,
                                    "source": source,
                                    "source_url": str(source_url),
                                    "budget": budget,
                                    "skills": skills,
                                    "finder_score": intel_score,
                                    "client": {
                                        "name": intel_data.get("client_intel", {}).get("contact", {}).get("name"),
                                        "company": intel_data.get("client_intel", {}).get("contact", {}).get("company"),
                                        "email": intel_data.get("client_intel", {}).get("contact", {}).get("email"),
                                    },
                                },
                            )
                            if messager_res.status_code in (200, 201):
                                proposals_staged += 1

                    except Exception as item_err:
                        errors.append(f"Failed processing lead '{item.get('title')}': {str(item_err)}")

        except Exception as e:
            errors.append(f"Pipeline execution failure: {str(e)}")
            self._log_step(run.id, "Pipeline Execution", "orchestrator", "failed", str(e), step_logs)

        # Update run model
        run.status = "completed" if not errors else "completed_with_warnings"
        run.leads_discovered_count = discovered_count
        run.leads_enriched_count = enriched_count
        run.leads_saved_count = saved_count
        run.proposals_staged_count = proposals_staged
        run.errors = errors
        run.finished_at = datetime.now(UTC)

        self.session.commit()

        return PipelineRunResponse(
            id=run.id,
            status=run.status,
            leads_discovered_count=discovered_count,
            leads_enriched_count=enriched_count,
            leads_saved_count=saved_count,
            proposals_staged_count=proposals_staged,
            errors=errors,
            started_at=run.started_at,
            finished_at=run.finished_at,
            steps=[WorkflowStepResponse.model_validate(s) for s in step_logs],
        )

    def _log_step(
        self,
        run_id: str,
        name: str,
        target: str,
        status: str,
        msg: str,
        step_logs: list[WorkflowStepLogModel],
    ) -> None:
        log = WorkflowStepLogModel(
            pipeline_run_id=run_id,
            step_name=name,
            service_target=target,
            status=status,
            message=msg,
            payload_json={},
        )
        self.session.add(log)
        step_logs.append(log)
