"""
Rate Limiter Middleware
========================
FastAPI rate limiting for API protection (Module C3).
"""

import time
from collections import defaultdict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter using sliding window.
    
    Limits requests per minute per client IP.
    """

    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.rpm_limit = settings.rate_limit_rpm
        self.burst_limit = settings.rate_limit_burst
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries (sliding window of 60s)
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < 60
        ]

        if len(self.requests[client_ip]) >= self.rpm_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response
