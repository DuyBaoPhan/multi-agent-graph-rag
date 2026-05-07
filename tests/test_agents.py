"""
Agent Tests
=============
Test multi-agent framework, session management, and concurrency (Module A2).
"""

import pytest

from src.agents.dispatcher import AgentDispatcher
from src.agents.session_store import SessionStore


class TestSessionStore:
    """Test session management."""

    def test_create_session(self):
        store = SessionStore()
        sid = store.create_session()
        assert sid is not None
        assert sid in store.sessions

    def test_add_and_get_history(self):
        store = SessionStore()
        sid = store.create_session()
        store.add_turn(sid, "Xin chào", "Chào bạn!")
        history = store.get_history(sid)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_history_limit(self):
        store = SessionStore()
        store.settings.session_max_history = 2
        sid = store.create_session()
        for i in range(5):
            store.add_turn(sid, f"Câu hỏi {i}", f"Trả lời {i}")
        history = store.get_history(sid)
        # Max 2 turns = 4 messages
        assert len(history) <= 4

    def test_cleanup_expired(self):
        store = SessionStore()
        store.settings.session_ttl_minutes = 0  # Expire immediately
        sid = store.create_session()
        store.sessions[sid]["last_active"] = 0  # Force expired
        store.cleanup_expired()
        assert sid not in store.sessions


class TestDispatcher:
    """Test agent dispatching."""

    @pytest.mark.asyncio
    async def test_dispatch_chitchat(self):
        dispatcher = AgentDispatcher()
        result = await dispatcher.dispatch("chitchat", "Xin chào!", [])
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_dispatch_unknown_intent(self):
        dispatcher = AgentDispatcher()
        result = await dispatcher.dispatch("unknown_intent", "test", [])
        assert isinstance(result, str)
