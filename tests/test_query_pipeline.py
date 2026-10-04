"""
tests/test_query_pipeline.py
----------------------------
Tests for the query pipeline: mock generation, self-correction, and safety handling.
"""

from unittest.mock import patch
import pytest
from app.services.query_pipeline import run_pipeline


@patch("app.services.query_pipeline.generate_sql")
def test_pipeline_successful_flow(mock_generate):
    mock_generate.return_value = "SELECT department_name FROM departments ORDER BY department_name ASC LIMIT 5;"
    result = run_pipeline("List top 5 departments")
    assert result["row_count"] > 0
    assert "columns" in result
    assert "rows" in result
    assert result["attempts"] == 1
    assert result["error"] is None


@patch("app.services.query_pipeline.generate_sql")
def test_pipeline_self_correction_on_syntax_error(mock_generate):
    # First call returns bad SQL, second returns fixed SQL
    mock_generate.side_effect = [
        "SELECT nonexistent_col_123 FROM departments;",
        "SELECT department_id, department_name FROM departments LIMIT 2;",
    ]
    result = run_pipeline("Show departments")
    assert result["row_count"] == 2
    assert result["attempts"] == 2
    assert "correction_history" in result
    assert len(result["correction_history"]) == 1


@patch("app.services.query_pipeline.generate_sql")
def test_pipeline_blocks_unsafe_sql(mock_generate):
    # Generates destructive SQL on all attempts
    mock_generate.return_value = "DROP TABLE employees;"
    result = run_pipeline("Delete employees")
    assert "error" in result
    assert "Could not produce a safe query" in result["error"]
