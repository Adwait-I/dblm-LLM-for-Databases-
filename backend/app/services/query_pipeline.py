"""
services/query_pipeline.py
--------------------------
End-to-end Text-to-SQL pipeline:
  1. Introspect schema  →  build DDL string
  2. Build LLM prompt   →  call Ollama
  3. Validate SQL safety
  4. Execute against the read-only engine
  5. Return results (or self-correct on SQL error up to MAX_SQL_RETRIES)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.database.connection import get_readonly_session
from app.llm.provider import generate_sql
from app.prompts.sql_prompt import build_system_prompt, build_user_prompt
from app.services.schema_introspector import schema_to_ddl_string
from app.utils.sql_safety import validate_sql

logger = get_logger(__name__)


def _execute_sql(sql: str) -> Dict[str, Any]:
    """
    Execute a read-only SQL query and return columns + rows.

    Returns:
        {"columns": [...], "rows": [[...], ...], "row_count": int}

    Raises:
        RuntimeError on execution failure.
    """
    with get_readonly_session() as session:
        result = session.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }


def _build_correction_prompt(
    question: str, failed_sql: str, error_msg: str
) -> str:
    """Build a follow-up prompt asking the LLM to fix the SQL."""
    return (
        f"The following SQL query was generated for the question:\n"
        f"Question: {question}\n\n"
        f"SQL:\n{failed_sql}\n\n"
        f"But it failed with this error:\n{error_msg}\n\n"
        f"Please generate a corrected PostgreSQL SELECT query. "
        f"Return ONLY the SQL — no commentary."
    )


def run_pipeline(question: str) -> Dict[str, Any]:
    """
    Full Text-to-SQL pipeline.

    Args:
        question: The user's natural-language question.

    Returns:
        A dict with keys: question, sql, columns, rows, row_count,
        attempts, execution_time_ms, and optionally correction_history.
    """
    start = time.time()

    # 1) Schema → DDL string
    schema_ddl = schema_to_ddl_string()

    # 2) Build prompts
    system_prompt = build_system_prompt(schema_ddl)
    user_prompt = build_user_prompt(question)

    # 3) Generate SQL via LLM
    sql = generate_sql(system_prompt, user_prompt)
    logger.info("Generated SQL", extra={"sql": sql})

    max_retries = settings.max_sql_retries
    attempts = 1
    correction_history: List[Dict[str, str]] = []

    for attempt in range(1, max_retries + 1):
        # 4) Validate safety
        is_safe, reason = validate_sql(sql)
        if not is_safe:
            logger.warning(
                "SQL safety check failed",
                extra={"attempt": attempt, "reason": reason, "sql": sql},
            )
            correction_history.append(
                {"sql": sql, "error": f"Safety violation: {reason}"}
            )
            # Ask LLM to correct
            correction = _build_correction_prompt(question, sql, reason)
            sql = generate_sql(system_prompt, correction)
            attempts += 1
            continue

        # 5) Execute
        try:
            result = _execute_sql(sql)
            elapsed_ms = round((time.time() - start) * 1000, 2)

            response: Dict[str, Any] = {
                "question": question,
                "sql": sql,
                "columns": result["columns"],
                "rows": result["rows"],
                "row_count": result["row_count"],
                "attempts": attempts,
                "execution_time_ms": elapsed_ms,
                "error": None,
            }
            if correction_history:
                response["correction_history"] = correction_history

            logger.info(
                "Query pipeline succeeded",
                extra={
                    "attempts": attempts,
                    "row_count": result["row_count"],
                    "ms": elapsed_ms,
                },
            )
            return response

        except Exception as exec_err:
            error_msg = str(exec_err)
            logger.warning(
                "SQL execution failed",
                extra={"attempt": attempt, "error": error_msg, "sql": sql},
            )
            correction_history.append({"sql": sql, "error": error_msg})

            if attempt < max_retries:
                correction = _build_correction_prompt(
                    question, sql, error_msg
                )
                sql = generate_sql(system_prompt, correction)
                attempts += 1
            else:
                elapsed_ms = round((time.time() - start) * 1000, 2)
                return {
                    "question": question,
                    "sql": sql,
                    "error": f"Query failed after {max_retries} attempts: {error_msg}",
                    "attempts": attempts,
                    "execution_time_ms": elapsed_ms,
                    "correction_history": correction_history,
                }

    # Exhausted retries on safety checks
    elapsed_ms = round((time.time() - start) * 1000, 2)
    return {
        "question": question,
        "sql": sql,
        "error": f"Could not produce a safe query after {max_retries} attempts.",
        "attempts": attempts,
        "execution_time_ms": elapsed_ms,
        "correction_history": correction_history,
    }
