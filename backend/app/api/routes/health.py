"""
api/routes/health.py
--------------------
Health-check endpoint.  Returns:
  - API status
  - PostgreSQL connectivity (primary + readonly engines)
  - LLM provider configuration
  - Application version / environment
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger
from app.database.connection import check_database_connectivity

router = APIRouter(prefix="/api", tags=["health"])
logger = get_logger(__name__)

# Application start time for uptime calculation
_START_TIME = time.time()


@router.get("/health", summary="Health check")
async def health_check():
    """
    Returns API health, PostgreSQL connectivity, and LLM config.
    Safe to call from monitoring tools — never returns 5xx on DB issues,
    it returns 200 with status detail instead so monitors can parse it.
    """
    db_status = check_database_connectivity()
    uptime_seconds = round(time.time() - _START_TIME, 1)

    primary_ok = db_status["primary"]["status"] == "connected"
    readonly_ok = db_status["readonly"]["status"] == "connected"
    overall = "healthy" if (primary_ok and readonly_ok) else "degraded"

    response = {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "app": {
            "name": settings.app_name,
            "env": settings.app_env,
            "version": "0.1.0-phase1",
        },
        "database": {
            "primary": db_status["primary"],
            "readonly": db_status["readonly"],
        },
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.ollama_model if settings.llm_provider == "ollama" else "configured",
            "base_url": settings.ollama_base_url if settings.llm_provider == "ollama" else None,
        },
    }

    logger.info(
        "Health check",
        extra={
            "status": overall,
            "db_primary": db_status["primary"]["status"],
            "db_readonly": db_status["readonly"]["status"],
        },
    )

    return response
