"""
Health Check Routes
====================
Endpoints for monitoring service health (Module C3).
"""

from fastapi import APIRouter
from loguru import logger

router = APIRouter()


@router.get("/health")
async def health_check():
    """Overall system health check."""
    # TODO: Check Neo4j, Redis, SGLang connections
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "neo4j": "unknown",
            "redis": "unknown",
            "sglang_router": "unknown",
            "sglang_generator": "unknown",
            "tei": "unknown",
        },
    }


@router.get("/health/{service}")
async def service_health(service: str):
    """Individual service health check."""
    # TODO: Implement per-service health checks
    return {"service": service, "status": "unknown"}
