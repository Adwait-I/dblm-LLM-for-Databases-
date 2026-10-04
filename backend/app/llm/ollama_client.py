"""
llm/ollama_client.py
--------------------
Ollama client wrapper (re-exports unified provider functions).
"""

from app.llm.provider import generate_sql, strip_sql_fences

__all__ = ["generate_sql", "strip_sql_fences"]
