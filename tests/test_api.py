"""
tests/test_api.py
-----------------
API integration tests using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "llm" in data


def test_schema_tables_endpoint():
    response = client.get("/api/schema/tables")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "tables" in data
    table_names = [t["name"] for t in data["tables"]]
    assert "employees" in table_names
    assert "departments" in table_names


def test_schema_relationships_endpoint():
    response = client.get("/api/schema/relationships")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "relationships" in data
    assert len(data["relationships"]) > 0


def test_invalid_query_validation():
    response = client.post("/api/query", json={"question": "   "})
    assert response.status_code == 422  # Pydantic validation error
