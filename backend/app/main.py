
"""
main.py
-------
FastAPI application entry point for QueryMind.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.api.routes import health, query, schema

# Initialise logging before anything else
setup_logging()
logger = get_logger(__name__)


# ------------------------------------------------------------------ #
# Lifespan — startup / shutdown hooks
# ------------------------------------------------------------------ #

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "QueryMind starting up",
        extra={"env": settings.app_env, "provider": settings.llm_provider},
    )
    yield
    logger.info("QueryMind shutting down")


# ------------------------------------------------------------------ #
# Application factory
# ------------------------------------------------------------------ #

app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic Natural Language Database Interface — "
        "converts plain-English questions to PostgreSQL queries."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------------ #
# CORS
# ------------------------------------------------------------------ #

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# Request timing middleware
# ------------------------------------------------------------------ #

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    return response


# ------------------------------------------------------------------ #
# Global exception handler (hides stack traces in production)
# ------------------------------------------------------------------ #

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", extra={"path": request.url.path, "error": str(exc)})
    detail = str(exc) if settings.is_development else "An internal error occurred."
    return JSONResponse(status_code=500, content={"detail": detail})


# ------------------------------------------------------------------ #
# Routers
# ------------------------------------------------------------------ #

app.include_router(health.router)
app.include_router(query.router)
app.include_router(schema.router)


# ------------------------------------------------------------------ #
# Root redirect
# ------------------------------------------------------------------ #

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/api/health",
    }
