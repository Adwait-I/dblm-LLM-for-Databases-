"""
tests/test_sql_safety.py
------------------------
Unit tests for the SQL safety validator.
"""

import pytest
from app.utils.sql_safety import validate_sql


def test_valid_select_queries():
    valid_queries = [
        "SELECT * FROM employees;",
        "SELECT first_name, last_name FROM employees WHERE department_id = 5",
        "SELECT d.department_name, count(e.employee_id) FROM departments d JOIN employees e ON d.department_id = e.department_id GROUP BY d.department_name",
        "WITH high_earners AS (SELECT * FROM employees WHERE salary > 10000) SELECT * FROM high_earners",
    ]
    for q in valid_queries:
        is_safe, reason = validate_sql(q)
        assert is_safe is True, f"Failed on safe query: {q} with reason: {reason}"


def test_forbidden_ddl_dml_queries():
    forbidden_queries = [
        "DROP TABLE employees;",
        "DELETE FROM employees WHERE employee_id = 1",
        "UPDATE employees SET salary = 1000000 WHERE employee_id = 1",
        "INSERT INTO departments (department_name) VALUES ('Hacking')",
        "ALTER TABLE employees ADD COLUMN test_col int",
        "TRUNCATE TABLE dependents",
        "GRANT ALL PRIVILEGES ON DATABASE DBMS_proj TO public",
    ]
    for q in forbidden_queries:
        is_safe, reason = validate_sql(q)
        assert is_safe is False, f"Expected forbidden query to fail: {q}"


def test_multiple_statements_blocked():
    multi_statement = "SELECT * FROM employees; DROP TABLE dependents;"
    is_safe, reason = validate_sql(multi_statement)
    assert is_safe is False
    assert "Forbidden keyword" in reason or "Multiple SQL statements" in reason


def test_empty_query():
    is_safe, reason = validate_sql("   ")
    assert is_safe is False
