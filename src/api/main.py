"""
FastAPI application for Client Orchestrator Service.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import events_router, health_router, topology_router, workflow_router
from src.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Client Orchestrator Service API",
        description="End-to-end workflow automation, event routing, pipeline coordination, and service discovery.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(workflow_router)
    app.include_router(events_router)
    app.include_router(topology_router)

    @app.get("/", tags=["Root"])
    def root() -> dict[str, str]:
        return {
            "service": "Client Orchestrator Service",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
