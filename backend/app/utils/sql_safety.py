"""
utils/sql_safety.py
-------------------
Validates that LLM-generated SQL is safe to execute against the
production database.  Only SELECT queries are allowed.
"""

from __future__ import annotations

import re
from typing import Tuple

import sqlparse

# Statements that MUST NOT appear — case-insensitive
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|"
    r"EXECUTE|EXEC|COPY|VACUUM|CLUSTER|REINDEX|COMMENT|LOCK|DISCARD|"
    r"SET\s+ROLE|SET\s+SESSION)\b",
    re.IGNORECASE,
)


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Check whether the SQL is a safe, read-only SELECT.

    Returns:
        (is_safe, reason)  — True with empty reason if safe;
                             False with an explanation if not.
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query."

    stripped = sql.strip().rstrip(";").strip()

    # Must start with SELECT or WITH (CTE)
    if not re.match(r"^\s*(SELECT|WITH)\b", stripped, re.IGNORECASE):
        return False, "Query must start with SELECT or WITH."

    # Must not contain forbidden keywords
    match = _FORBIDDEN_KEYWORDS.search(stripped)
    if match:
        return False, f"Forbidden keyword detected: {match.group(0).upper()}"

    # Must not contain multiple statements (semicolons inside the query)
    parsed = sqlparse.parse(stripped)
    if len(parsed) > 1:
        return False, "Multiple SQL statements are not allowed."

    return True, ""
