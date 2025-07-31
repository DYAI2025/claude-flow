import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.marker import Marker, Frame

client = TestClient(app)

@pytest.fixture
def sample_marker():
    return {
        "_id": "TEST_MARKER_001",
        "frame": {
            "signal": ["test signal"],
            "concept": "test",
            "pragmatics": "testing",
            "narrative": "test_narrative"
        },
        "examples": ["Test example 1", "Test example 2"],
        "pattern": ["test pattern"],
        "activation": {"rule": "ANY 1 IN 1 messages"},
        "scoring": {"base": 1.0, "weight": 1.2},
        "tags": ["test", "sample"]
    }

def test_create_marker(sample_marker):
    with patch("app.services.marker_service.marker_collection.insert_one", new_callable=AsyncMock) as mock_insert:
        mock_insert.return_value = AsyncMock(inserted_id="TEST_MARKER_001")
        
        response = client.post("/markers/", json=sample_marker)
        assert response.status_code == 201
        assert response.json()["id"] == "TEST_MARKER_001"

def test_list_markers():
    with patch("app.services.marker_service.marker_collection.find") as mock_find:
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list.return_value = []
        mock_find.return_value = mock_cursor
        
        response = client.get("/markers/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_get_marker(sample_marker):
    with patch("app.services.marker_service.marker_collection.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = sample_marker
        
        response = client.get("/markers/TEST_MARKER_001")
        assert response.status_code == 200
        assert response.json()["id"] == "TEST_MARKER_001"

def test_get_marker_not_found():
    with patch("app.services.marker_service.marker_collection.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = None
        
        response = client.get("/markers/NONEXISTENT")
        assert response.status_code == 404