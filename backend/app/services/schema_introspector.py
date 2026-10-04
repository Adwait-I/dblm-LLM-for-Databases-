"""
services/schema_introspector.py
-------------------------------
Introspects the connected PostgreSQL database to extract:
  - table names
  - column details (name, type, nullable, default)
  - primary keys
  - foreign-key relationships

This information is fed into the LLM prompt so it can generate
correct SQL against the real schema.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import inspect, text

from app.core.logging import get_logger
from app.database.connection import engine

logger = get_logger(__name__)


def get_table_names() -> List[str]:
    """Return a sorted list of public-schema table names."""
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names(schema="public"))
    logger.info("Introspected table names", extra={"count": len(tables)})
    return tables


def get_table_columns(table_name: str) -> List[Dict[str, Any]]:
    """Return column metadata for a single table."""
    inspector = inspect(engine)
    raw_cols = inspector.get_columns(table_name, schema="public")
    columns = []
    for col in raw_cols:
        columns.append(
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col["default"]) if col.get("default") else None,
            }
        )
    return columns


def get_primary_keys(table_name: str) -> List[str]:
    """Return the primary-key column names for a table."""
    inspector = inspect(engine)
    pk = inspector.get_pk_constraint(table_name, schema="public")
    return pk.get("constrained_columns", [])


def get_foreign_keys() -> List[Dict[str, Any]]:
    """
    Return all foreign-key relationships across all public tables.
    Each entry: {table, column, ref_table, ref_column}.
    """
    inspector = inspect(engine)
    relationships: List[Dict[str, Any]] = []
    for table_name in inspector.get_table_names(schema="public"):
        fks = inspector.get_foreign_keys(table_name, schema="public")
        for fk in fks:
            for col, ref_col in zip(
                fk["constrained_columns"], fk["referred_columns"]
            ):
                relationships.append(
                    {
                        "table": table_name,
                        "column": col,
                        "ref_table": fk["referred_table"],
                        "ref_column": ref_col,
                    }
                )
    logger.info(
        "Introspected foreign keys", extra={"count": len(relationships)}
    )
    return relationships


def get_row_counts() -> Dict[str, int]:
    """Return approximate row counts for every public table."""
    counts: Dict[str, int] = {}
    with engine.connect() as conn:
        for table in get_table_names():
            row = conn.execute(
                text(f"SELECT COUNT(*) FROM public.\"{table}\"")
            ).fetchone()
            counts[table] = row[0] if row else 0
    return counts


def get_full_schema() -> Dict[str, Any]:
    """
    Assemble the complete schema context dict used by the LLM prompt builder.
    """
    tables_info: List[Dict[str, Any]] = []
    for table_name in get_table_names():
        tables_info.append(
            {
                "name": table_name,
                "columns": get_table_columns(table_name),
                "primary_keys": get_primary_keys(table_name),
            }
        )

    return {
        "tables": tables_info,
        "relationships": get_foreign_keys(),
    }


def schema_to_ddl_string() -> str:
    """
    Convert the live schema into a compact DDL-like text block
    suitable for embedding in an LLM prompt.
    """
    schema = get_full_schema()
    lines: List[str] = []

    for tbl in schema["tables"]:
        col_defs = []
        for c in tbl["columns"]:
            nullable = "" if c["nullable"] else " NOT NULL"
            pk = " PRIMARY KEY" if c["name"] in tbl["primary_keys"] else ""
            col_defs.append(f"  {c['name']} {c['type']}{nullable}{pk}")

        lines.append(f"CREATE TABLE {tbl['name']} (")
        lines.append(",\n".join(col_defs))
        lines.append(");")
        lines.append("")

    if schema["relationships"]:
        lines.append("-- Foreign Key Relationships:")
        for rel in schema["relationships"]:
            lines.append(
                f"-- {rel['table']}.{rel['column']} -> "
                f"{rel['ref_table']}.{rel['ref_column']}"
            )

    return "\n".join(lines)
