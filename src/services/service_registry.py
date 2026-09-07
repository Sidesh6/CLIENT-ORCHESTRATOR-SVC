"""
Service Discovery and Health Monitoring across all 5 platform services.
"""

import time
from datetime import UTC, datetime
import httpx
from src.config.settings import settings
from src.schemas.topology import PlatformTopologyResponse, ServiceStatus


class ServiceRegistry:
    """Monitors connectivity and latency of the 5 platform services."""

    def __init__(self) -> None:
        self.services_map = {
            "client-finder-svc": settings.finder_svc_url,
            "client-messager-svc": settings.messager_svc_url,
            "client-intelligence-svc": settings.intelligence_svc_url,
            "client-core-svc": settings.core_svc_url,
            "client-orchestrator-svc": f"http://localhost:{settings.app_port}",
        }

    def check_service(self, name: str, url: str) -> ServiceStatus:
        health_url = f"{url.rstrip('/')}/health"
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=2.5) as client:
                res = client.get(health_url)
                latency = round((time.perf_counter() - start) * 1000, 1)
                if res.status_code == 200:
                    return ServiceStatus(
                        name=name,
                        url=url,
                        status="online",
                        latency_ms=latency,
                        last_checked=datetime.now(UTC),
                    )
                else:
                    return ServiceStatus(
                        name=name,
                        url=url,
                        status="degraded",
                        latency_ms=latency,
                        last_checked=datetime.now(UTC),
                    )
        except Exception:
            return ServiceStatus(
                name=name,
                url=url,
                status="offline",
                latency_ms=None,
                last_checked=datetime.now(UTC),
            )

    def get_topology(self) -> PlatformTopologyResponse:
        statuses: list[ServiceStatus] = []
        online = 0
        for name, url in self.services_map.items():
            status = self.check_service(name, url)
            if status.status == "online":
                online += 1
            statuses.append(status)

        return PlatformTopologyResponse(
            platform_name="Client AI 5-Service Platform",
            total_services=len(self.services_map),
            online_count=online,
            services=statuses,
            checked_at=datetime.now(UTC),
        )


GLOBAL_REGISTRY = ServiceRegistry()
