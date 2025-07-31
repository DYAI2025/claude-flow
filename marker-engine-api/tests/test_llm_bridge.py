import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm_bridge import LLMBridge, MarkerInterpretation, LLMResponse
import httpx


@pytest.fixture
def llm_bridge():
    """Create LLM bridge instance"""
    with patch.dict('os.environ', {
        'KIMI_API_KEY': 'test_kimi_key',
        'OPENAI_API_KEY': 'test_openai_key'
    }):
        return LLMBridge()


@pytest.fixture
def sample_marker_data():
    """Sample marker interpretation data"""
    return MarkerInterpretation(
        markers=[
            {
                "id": "TEST_MARKER_1",
                "frame": {
                    "concept": "anxiety",
                    "signal": ["worried", "concerned"],
                    "pragmatics": "emotional_state",
                    "narrative": "personal"
                },
                "scoring": {"base": 1.5, "weight": 1.2}
            },
            {
                "id": "TEST_MARKER_2",
                "frame": {
                    "concept": "avoidance",
                    "signal": ["but", "however"],
                    "pragmatics": "relational",
                    "narrative": "distancing"
                },
                "scoring": {"base": 1.0, "weight": 1.5}
            }
        ],
        schema_name="test_schema",
        detected_count=2,
        total_score=3.3
    )


@pytest.mark.asyncio
async def test_kimi_api_success(llm_bridge, sample_marker_data):
    """Test successful Kimi API call"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "Test interpretation from Kimi"
            }
        }]
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await llm_bridge.generate_interpretation(sample_marker_data)
        
        assert result.interpretation == "Test interpretation from Kimi"
        assert result.model_used == "moonshot-v1-128k"
        assert result.processing_time > 0
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_openai_fallback(llm_bridge, sample_marker_data):
    """Test fallback to OpenAI when Kimi fails"""
    # Kimi fails
    kimi_response = MagicMock()
    kimi_response.status_code = 500
    
    # OpenAI succeeds
    openai_response = MagicMock()
    openai_response.status_code = 200
    openai_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "Test interpretation from GPT-4"
            }
        }]
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [kimi_response, openai_response]
        
        result = await llm_bridge.generate_interpretation(sample_marker_data)
        
        assert result.interpretation == "Test interpretation from GPT-4"
        assert result.model_used == "gpt-4"
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_both_apis_fail(llm_bridge, sample_marker_data):
    """Test default interpretation when both APIs fail"""
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Network error")
        
        result = await llm_bridge.generate_interpretation(sample_marker_data)
        
        assert "2 bedeutsame Marker" in result.interpretation
        assert result.model_used == "default"


@pytest.mark.asyncio
async def test_no_api_keys():
    """Test behavior when API keys are not configured"""
    with patch.dict('os.environ', {}, clear=True):
        bridge = LLMBridge()
        
        marker_data = MarkerInterpretation(
            markers=[],
            schema_name="test",
            detected_count=0,
            total_score=0.0
        )
        
        result = await bridge.generate_interpretation(marker_data)
        
        assert result.model_used == "default"
        assert "technischer Einschränkungen" in result.interpretation