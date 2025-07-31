"""
Unit tests for OrchestrationService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.orchestration_service import OrchestrationService
from app.models.analysis_context import AnalysisContext


@pytest.fixture
def orchestration_service():
    """Create OrchestrationService instance with mocked dependencies"""
    with patch('app.services.orchestration_service.MarkerService') as mock_marker_service:
        with patch('app.services.orchestration_service.get_nlp_service') as mock_get_nlp:
            # Create mock instances
            marker_service = AsyncMock()
            nlp_service = Mock()
            
            # Configure mocks
            mock_marker_service.return_value = marker_service
            mock_get_nlp.return_value = nlp_service
            
            # Create service
            service = OrchestrationService()
            service.marker_service = marker_service
            service.nlp_service = nlp_service
            
            return service, marker_service, nlp_service


@pytest.mark.asyncio
async def test_analyze_basic_flow(orchestration_service):
    """Test basic analysis flow through all phases"""
    service, marker_service, nlp_service = orchestration_service
    
    # Configure mocks
    marker_service.initial_scan.return_value = [
        {
            "marker_id": "A_EMOTION_MISSING",
            "marker_type": "A",
            "confidence": 0.8
        }
    ]
    
    marker_service.contextual_rescan.return_value = [
        {
            "marker_id": "C_AMBIVALENCE",
            "marker_type": "C",
            "confidence": 0.9
        }
    ]
    
    nlp_service.is_available.return_value = True
    nlp_service.enrich = Mock()  # In-place modification
    
    # Run analysis
    result = await service.analyze(
        text="Ich vermisse dich, aber ich brauche Abstand.",
        schema_id="relationship"
    )
    
    # Verify result structure
    assert result['status'] == 'success'
    assert 'request_id' in result
    assert 'markers' in result
    assert 'performance_metrics' in result
    assert 'metadata' in result
    
    # Verify service calls
    marker_service.initial_scan.assert_called_once()
    nlp_service.enrich.assert_called_once()
    marker_service.contextual_rescan.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_without_nlp(orchestration_service):
    """Test analysis when NLP service is unavailable"""
    service, marker_service, nlp_service = orchestration_service
    
    # Configure NLP as unavailable
    nlp_service.is_available.return_value = False
    
    marker_service.initial_scan.return_value = [
        {"marker_id": "A_TEST", "marker_type": "A"}
    ]
    marker_service.contextual_rescan.return_value = []
    
    # Run analysis
    result = await service.analyze(text="Test text")
    
    # Verify NLP was skipped
    assert result['nlp_enriched'] is False
    assert result['metadata'].get('nlp_skipped') is True
    
    # Phase 3 should be skipped
    marker_service.contextual_rescan.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_error_handling(orchestration_service):
    """Test error handling in analysis pipeline"""
    service, marker_service, nlp_service = orchestration_service
    
    # Configure phase 1 to fail
    marker_service.initial_scan.side_effect = Exception("Database error")
    
    # Run analysis
    result = await service.analyze(text="Test text")
    
    # Should return error result
    assert result['status'] == 'error'
    assert 'Database error' in result['error']
    assert result['markers'] == []


@pytest.mark.asyncio
async def test_phase_timing_metrics(orchestration_service):
    """Test that timing metrics are collected for each phase"""
    service, marker_service, nlp_service = orchestration_service
    
    # Configure successful responses
    marker_service.initial_scan.return_value = []
    marker_service.contextual_rescan.return_value = []
    nlp_service.is_available.return_value = True
    
    # Run analysis
    result = await service.analyze(text="Test")
    
    # Check performance metrics
    metrics = result['performance_metrics']
    assert 'phase1_initial_scan' in metrics
    assert 'phase2_nlp_enrichment' in metrics
    assert 'phase3_contextual_rescan' in metrics
    assert 'total' in metrics
    
    # All timings should be positive
    for phase, timing in metrics.items():
        assert timing >= 0


@pytest.mark.asyncio
async def test_marker_merging(orchestration_service):
    """Test merging of markers from different phases"""
    service, marker_service, nlp_service = orchestration_service
    
    # Initial markers
    initial_markers = [
        {"marker_id": "A_1", "confidence": 0.6},
        {"marker_id": "S_1", "confidence": 0.7}
    ]
    
    # Contextual markers (including confidence update)
    contextual_markers = [
        {"marker_id": "C_1", "confidence": 0.8},  # New marker
        {"marker_id": "A_1", "confidence": 0.9}   # Update existing
    ]
    
    marker_service.initial_scan.return_value = initial_markers
    marker_service.contextual_rescan.return_value = contextual_markers
    nlp_service.is_available.return_value = True
    
    # Run analysis
    result = await service.analyze(text="Test")
    
    # Should have 3 markers total
    assert len(result['markers']) == 3
    
    # A_1 should have updated confidence
    a1_marker = next(m for m in result['markers'] if m['marker_id'] == 'A_1')
    assert a1_marker['confidence'] == 0.9
    assert a1_marker.get('confidence_updated') is True


@pytest.mark.asyncio 
async def test_batch_analysis(orchestration_service):
    """Test batch analysis functionality"""
    service, marker_service, nlp_service = orchestration_service
    
    # Configure mocks
    marker_service.initial_scan.return_value = []
    marker_service.contextual_rescan.return_value = []
    nlp_service.is_available.return_value = True
    
    # Run batch analysis
    texts = ["Text 1", "Text 2", "Text 3"]
    results = await service.analyze_batch(texts, schema_id="test")
    
    # Should return list of results
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result['text'] == texts[i]
        assert result['status'] == 'success'


def test_service_status(orchestration_service):
    """Test service status reporting"""
    service, marker_service, nlp_service = orchestration_service
    
    nlp_service.is_available.return_value = True
    nlp_service.__class__.__name__ = 'DummyNlpService'
    
    # Get status
    status = service.get_service_status()
    
    # Verify status structure
    assert status['orchestration_service'] == 'active'
    assert status['marker_service'] == 'active'
    assert status['nlp_service']['available'] is True
    assert 'phases_enabled' in status