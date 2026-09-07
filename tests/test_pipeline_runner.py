from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from src.schemas.workflow import PipelineRunRequest
from src.services.service_registry import ServiceRegistry
from src.workflows.pipeline_runner import PipelineRunner


def test_service_registry_check():
    registry = ServiceRegistry()
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        status = registry.check_service("client-finder-svc", "http://localhost:8000")
        assert status.status == "online"
        assert status.latency_ms is not None


def test_pipeline_runner_orchestration(db_session: Session):
    runner = PipelineRunner(db_session)

    mock_finder_projects = [
        {
            "id": "FINDER-1",
            "title": "FastAPI & RAG Pipeline Developer",
            "description": "Construct pgvector document pipeline with Python",
            "source": "Hacker News",
            "source_url": "https://hn.com/1",
            "budget": 4500.0,
            "skills": ["FastAPI", "Python", "RAG"],
            "score": 90.0,
        }
    ]

    mock_intel_response = {
        "requirements": {"primary_technologies": ["FastAPI", "Python"]},
        "client_intel": {"contact": {"name": "Alex", "company": "AI Labs", "email": "alex@ailabs.io"}},
        "scoring": {"score": {"overall_score": 91.0}},
    }

    with patch("httpx.Client.get") as mock_get, patch("httpx.Client.post") as mock_post:
        # Mock Finder GET
        mock_finder_res = MagicMock()
        mock_finder_res.status_code = 200
        mock_finder_res.json.return_value = {"items": mock_finder_projects}
        mock_get.return_value = mock_finder_res

        # Mock downstream POSTs
        mock_intel_res = MagicMock()
        mock_intel_res.status_code = 200
        mock_intel_res.json.return_value = mock_intel_response

        mock_core_res = MagicMock()
        mock_core_res.status_code = 201
        mock_core_res.json.return_value = {"id": "CORE-LEAD-1"}

        mock_messager_res = MagicMock()
        mock_messager_res.status_code = 201
        mock_messager_res.json.return_value = {"status": "success"}

        def side_effect_post(url, **kwargs):
            if "analyze" in url:
                return mock_intel_res
            elif "leads" in url:
                return mock_core_res
            elif "ingest" in url:
                return mock_messager_res
            return mock_core_res

        mock_post.side_effect = side_effect_post

        req = PipelineRunRequest(min_qualification_score=75.0, limit=5)
        res = runner.run_pipeline(req)

        assert res.leads_discovered_count == 1
        assert res.leads_enriched_count == 1
        assert res.leads_saved_count == 1
        assert res.proposals_staged_count == 1
        assert res.status == "completed"
