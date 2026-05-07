"""
FastAPI Gateway - Main Application
====================================
Entry point for the Highlands Coffee Multi-Agent Robot API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config import get_settings
from src.gateway.routes import chat, health, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    logger.info("🚀 Starting Highlands Coffee Multi-Agent Robot...")
    logger.info(f"   Neo4j: {settings.neo4j_uri}")
    logger.info(f"   Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"   SGLang Router: {settings.sglang_router_host}")
    logger.info(f"   SGLang Generator: {settings.sglang_generator_host}")

    # TODO: Initialize connections (Neo4j, Redis, SGLang clients)

    yield

    # TODO: Cleanup connections
    logger.info("👋 Shutting down Highlands Coffee Multi-Agent Robot...")


app = FastAPI(
    title="Highlands Coffee Multi-Agent Robot",
    description="Production-ready Multi-Agent LLM System with Graph RAG",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
