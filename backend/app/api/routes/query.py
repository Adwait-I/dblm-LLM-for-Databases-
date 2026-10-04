
"""
api/routes/query.py
-------------------
POST /api/query — accepts a natural-language question,
runs the Text-to-SQL pipeline, and returns results.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.core.logging import get_logger
from app.services.query_pipeline import run_pipeline

router = APIRouter(prefix="/api", tags=["query"])
logger = get_logger(__name__)


class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question must not be empty.")
        return v.strip()


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list | None = None
    rows: list | None = None
    row_count: int | None = None
    attempts: int = 1
    execution_time_ms: float | None = None
    error: str | None = None
    correction_history: list | None = None


@router.post(
    "/query",
    summary="Natural-language to SQL query",
    response_model=QueryResponse,
)
async def query(request: QueryRequest):
    """
    Accepts a natural-language question, generates SQL via the LLM,
    validates it, executes it against the database, and returns the results.
    Self-corrects on SQL errors up to MAX_SQL_RETRIES times.
    """
    logger.info("Query received", extra={"question": request.question})

    try:
        result = run_pipeline(request.question)
        return QueryResponse(**result)
    except Exception as exc:
        logger.error(
            "Query pipeline error",
            extra={"question": request.question, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=str(exc))
