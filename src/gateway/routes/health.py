"""
Health Check Routes
====================
Endpoints for monitoring service health (Module C3).
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Overall system health check."""
    neo4j_health = {"status": "unknown"}
    redis_health = {"status": "unknown"}

    if hasattr(request.app.state, "neo4j"):
        neo4j_health = await request.app.state.neo4j.health_check()
    if hasattr(request.app.state, "redis"):
        redis_health = await request.app.state.redis.health_check()

    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "neo4j": neo4j_health,
            "redis": redis_health,
            "sglang_router": "not_connected",
            "sglang_generator": "not_connected",
        },
    }
