from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_health_and_topology_api(client: TestClient):
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["service"] == "client-orchestrator-svc"

    from src.schemas.topology import ServiceStatus
    from datetime import UTC, datetime
    with patch("src.services.service_registry.ServiceRegistry.check_service") as mock_check:
        mock_check.return_value = ServiceStatus(
            name="mock-svc",
            url="http://localhost:8000",
            status="online",
            latency_ms=1.5,
            last_checked=datetime.now(UTC),
        )

        top_res = client.get("/api/v1/topology")
        assert top_res.status_code == 200
        data = top_res.json()
        assert data["total_services"] == 5
        assert data["online_count"] == 5


def test_emit_event_api(client: TestClient):
    res = client.post(
        "/api/v1/events/emit",
        json={
            "event_type": "lead.qualified",
            "source_service": "client-core-svc",
            "entity_id": "LEAD-99",
            "data": {"score": 88.0},
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "published"
