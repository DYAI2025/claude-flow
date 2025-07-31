import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app

client = TestClient(app)

def test_analyze_text():
    with patch("app.services.analyze_service.detector_collection.find") as mock_find:
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {
                "_id": "detector_1",
                "id": "test_detector",
                "file_path": "test_detector.py",
                "fires_marker": "TEST_MARKER_001"
            }
        ]
        mock_find.return_value = mock_cursor
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            with patch("importlib.util.spec_from_file_location") as mock_spec:
                mock_module = MagicMock()
                mock_module.detect = MagicMock(return_value=True)
                
                mock_spec_obj = MagicMock()
                mock_spec_obj.loader.exec_module = MagicMock()
                mock_spec.return_value = mock_spec_obj
                
                with patch("importlib.util.module_from_spec") as mock_module_from_spec:
                    mock_module_from_spec.return_value = mock_module
                    
                    response = client.post("/analyze/", json={
                        "text": "Test text for analysis",
                        "schema_id": "test_schema"
                    })
                    
                    assert response.status_code == 200
                    assert "markers" in response.json()
                    assert response.json()["interpretation"] == "Analysis complete."