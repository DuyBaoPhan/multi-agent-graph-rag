"""
Global configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Neo4j ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "highlands2024"
    neo4j_database: str = "neo4j"

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # --- SGLang ---
    sglang_router_host: str = "http://localhost:30000"
    sglang_generator_host: str = "http://localhost:30001"

    # --- TEI ---
    tei_host: str = "http://localhost:8080"

    # --- FastAPI ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # --- Session ---
    session_ttl_minutes: int = 30
    session_max_history: int = 5
    session_context_threshold: float = 0.7

    # --- Rate Limiting ---
    rate_limit_rpm: int = 60
    rate_limit_burst: int = 10

    # --- Cache ---
    semantic_cache_threshold: float = 0.92
    cache_ttl_seconds: int = 3600

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
