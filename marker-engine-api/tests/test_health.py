from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import pytest
from app.main import app

client = TestClient(app)

def test_health_check_success():
    # Mock the database ping to succeed
    with patch("app.services.health_service.db.command", new_callable=AsyncMock) as mock_command:
        mock_command.return_value = True
        response = client.get("/healthz")
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["api_status"] == "ok"
        assert json_response["database_connected"] is True

def test_health_check_failure():
    # Mock the database ping to fail
    with patch("app.services.health_service.db.command", new_callable=AsyncMock) as mock_command:
        mock_command.side_effect = Exception("Connection failed")
        response = client.get("/healthz")
        assert response.status_code == 503
        assert response.json()["detail"] == "Database connection failed"