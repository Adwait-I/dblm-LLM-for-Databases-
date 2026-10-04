"""
api/routes/schema.py
--------------------
Schema introspection endpoints.
Exposes the real database structure so the frontend can display
table/column info and relationships.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.services.schema_introspector import (
    get_foreign_keys,
    get_full_schema,
    get_row_counts,
    get_table_columns,
    get_table_names,
    get_primary_keys,
)

router = APIRouter(prefix="/api/schema", tags=["schema"])
logger = get_logger(__name__)


@router.get("", summary="Full database schema")
async def get_schema():
    """Return the complete schema (tables, columns, PKs, FKs)."""
    try:
        schema = get_full_schema()
        return {"status": "ok", "schema": schema}
    except Exception as exc:
        logger.error("Schema introspection failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/tables", summary="List all tables")
async def get_tables():
    """Return a list of table names with their column counts and row counts."""
    try:
        tables = get_table_names()
        row_counts = get_row_counts()
        result = []
        for t in tables:
            cols = get_table_columns(t)
            pks = get_primary_keys(t)
            result.append(
                {
                    "name": t,
                    "column_count": len(cols),
                    "row_count": row_counts.get(t, 0),
                    "primary_keys": pks,
                }
            )
        return {"status": "ok", "tables": result}
    except Exception as exc:
        logger.error("Table listing failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/tables/{table_name}", summary="Table detail")
async def get_table_detail(table_name: str):
    """Return columns and PKs for a specific table."""
    try:
        all_tables = get_table_names()
        if table_name not in all_tables:
            raise HTTPException(
                status_code=404, detail=f"Table '{table_name}' not found."
            )
        columns = get_table_columns(table_name)
        pks = get_primary_keys(table_name)
        return {
            "status": "ok",
            "table": table_name,
            "columns": columns,
            "primary_keys": pks,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Table detail failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/relationships", summary="Foreign-key relationships")
async def get_relationships():
    """Return all foreign-key relationships in the database."""
    try:
        rels = get_foreign_keys()
        return {"status": "ok", "relationships": rels}
    except Exception as exc:
        logger.error("FK introspection failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))
