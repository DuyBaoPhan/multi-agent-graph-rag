"""
End-to-End Tests
==================
Full pipeline integration tests.
Requires all services running (docker compose up).
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.mark.skip(reason="Requires full stack running")
class TestE2E:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}/health")
            assert r.status_code == 200
            assert r.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_chat_endpoint(self):
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/api/v1/chat",
                json={"message": "Xin chào"},
            )
            assert r.status_code == 200
            data = r.json()
            assert "reply" in data
            assert "session_id" in data

    @pytest.mark.asyncio
    async def test_multi_turn_context(self):
        """5 turns liên tục không mất context."""
        async with httpx.AsyncClient() as client:
            session_id = None
            for i in range(5):
                r = await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "message": f"Câu hỏi lần {i+1}",
                        "session_id": session_id,
                    },
                )
                assert r.status_code == 200
                session_id = r.json()["session_id"]

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """3 requests đồng thời không OOM."""
        import asyncio

        async with httpx.AsyncClient() as client:
            tasks = [
                client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"message": f"Request {i}"},
                )
                for i in range(3)
            ]
            results = await asyncio.gather(*tasks)
            for r in results:
                assert r.status_code == 200
