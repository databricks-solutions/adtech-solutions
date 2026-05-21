"""Integration tests for FastAPI endpoints using httpx AsyncClient and ASGITransport."""

import pytest
import httpx

from backend.main import app
from backend.services.databricks_client import get_databricks_client


class MockDatabricksClient:
    """Mock client that reports not configured so preview returns in-memory SQL only."""

    is_configured = False


@pytest.fixture
async def client():
    """Async HTTP client with no overrides."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def client_no_databricks():
    """Async HTTP client with get_databricks_client overridden via dependency_overrides."""
    mock = MockDatabricksClient()

    def get_mock_client():
        return mock  # type: ignore[return-value]

    app.dependency_overrides[get_databricks_client] = get_mock_client
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_databricks_client, None)


@pytest.mark.asyncio
async def test_get_features_returns_list(client):
    """GET /api/features returns feature list (no Databricks required)."""
    response = await client.get("/api/features")
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    features = data["features"]
    assert isinstance(features, list)
    assert len(features) > 0
    first = features[0]
    assert "name" in first
    assert "display_name" in first
    assert "column" in first
    assert "type" in first
    assert "operators" in first


@pytest.mark.asyncio
async def test_get_health_returns_ok(client):
    """GET /api/health returns status and model_endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "databricks_connected" in data
    assert "model_endpoint" in data


@pytest.mark.asyncio
async def test_post_segment_preview_without_databricks_returns_mock_counts(
    client_no_databricks,
):
    """POST /api/segment/preview when Databricks not configured returns 0 counts and SQL."""
    payload = {
        "segment": {
            "name": "test",
            "description": "Test segment",
            "groups": [
                {
                    "id": "g1",
                    "logic": "AND",
                    "conditions": [
                        {
                            "id": "c1",
                            "feature": "state",
                            "operator": "IS",
                            "values": ["CA"],
                        }
                    ],
                }
            ],
            "group_logic": "AND",
        },
        "include_sql": True,
    }
    response = await client_no_databricks.post("/api/segment/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["individual_count"] == 0
    assert data["household_count"] == 0
    assert "sql" in data
    assert data["sql"] is not None
    assert "state = 'CA'" in data["sql"]
    assert "megacorp_indid" in data["sql"] or "individual_count" in data["sql"].lower()


@pytest.mark.asyncio
async def test_post_segment_preview_invalid_condition_returns_400(client_no_databricks):
    """POST /api/segment/preview with invalid column returns 400."""
    payload = {
        "segment": {
            "name": "test",
            "description": "Bad",
            "groups": [
                {
                    "id": "g1",
                    "logic": "AND",
                    "conditions": [
                        {
                            "id": "c1",
                            "feature": "invalid_column",
                            "operator": "IS",
                            "values": ["x"],
                        }
                    ],
                }
            ],
            "group_logic": "AND",
        },
        "include_sql": True,
    }
    response = await client_no_databricks.post("/api/segment/preview", json=payload)
    assert response.status_code == 400
