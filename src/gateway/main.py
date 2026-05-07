"""
FastAPI Gateway — Main Application
====================================
Entry point with all services initialized.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.config import get_settings
from src.gateway.routes import chat, health, ingest, audio
from src.graph_rag.neo4j_client import Neo4jClient
from src.graph_rag.knowledge_store import get_knowledge_store
from src.llm_serving.cache.redis_cache import RedisCache
from src.agents.session_store import SessionStore

neo4j_client = Neo4jClient()
redis_cache = RedisCache()
session_store = SessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Highlands Coffee Multi-Agent Robot...")

    # Load knowledge store (menu + FAQ)
    store = get_knowledge_store()
    logger.info(f"   Knowledge: {len(store.menu_items)} menu items, {len(store.faq_entries)} FAQ entries")

    # Connect services (auto-fallback)
    await neo4j_client.connect()
    await redis_cache.connect()
    await session_store.start_cleanup_loop()

    app.state.neo4j = neo4j_client
    app.state.redis = redis_cache
    app.state.session_store = session_store
    app.state.knowledge = store

    neo4j_h = await neo4j_client.health_check()
    redis_h = await redis_cache.health_check()
    logger.info(f"   Neo4j: {neo4j_h['status']} ({neo4j_h.get('type','')})")
    logger.info(f"   Redis: {redis_h['status']} ({redis_h.get('type','')})")
    logger.info("✅ All systems ready!")

    yield

    await session_store.stop_cleanup_loop()
    await redis_cache.close()
    await neo4j_client.close()
    logger.info("👋 Shutdown complete.")


app = FastAPI(
    title="Highlands Coffee Multi-Agent Robot",
    description="Production-ready Multi-Agent LLM System with Graph RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio"])

# Mount demo UI
app.mount("/demo", StaticFiles(directory="demo", html=True), name="demo")
