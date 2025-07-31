"""
Tests for the NLP service abstraction.
"""
import pytest
import os
from app.models.analysis_context import AnalysisContext
from app.services.nlp_service import (
    NlpService,
    DummyNlpService,
    SparkNlpService,
    NlpServiceFactory,
    get_nlp_service
)


class TestNlpService:
    """Test cases for NLP service implementations."""
    
    def test_dummy_nlp_service_basic(self):
        """Test that DummyNlpService performs basic tokenization."""
        service = DummyNlpService()
        context = AnalysisContext(
            text="Ich vermisse dich, aber ich brauche Abstand.",
            schema_id="test_schema"
        )
        
        # Service should be available
        assert service.is_available()
        
        # Enrich the context
        service.enrich(context)
        
        # Check that tokens were added
        assert context.tokens is not None
        assert len(context.tokens) == 8  # Simple whitespace tokenization
        assert context.tokens[0] == "Ich"
        assert context.tokens[-1] == "Abstand."
        
        # Check sentences
        assert context.sentences == ["Ich vermisse dich, aber ich brauche Abstand."]
        
        # Check metadata
        assert context.metadata["nlp_service"] == "dummy"
        assert context.metadata["nlp_version"] == "1.0.0"
    
    def test_dummy_nlp_service_empty_text(self):
        """Test DummyNlpService with empty text."""
        service = DummyNlpService()
        context = AnalysisContext(text="", schema_id="test_schema")
        
        service.enrich(context)
        
        assert context.tokens == []
        assert context.sentences == [""]
    
    def test_spark_nlp_service_unavailable(self):
        """Test SparkNlpService when Spark NLP is not installed."""
        service = SparkNlpService()
        
        # If Spark NLP is not installed, service should not be available
        # (This test assumes Spark NLP is not installed in the test environment)
        if not service.is_available():
            context = AnalysisContext(
                text="Test text",
                schema_id="test_schema"
            )
            
            service.enrich(context)
            
            # Should fall back to basic processing
            assert context.tokens == ["Test", "text"]
            assert context.sentences == ["Test text"]
    
    def test_nlp_factory_default(self):
        """Test NlpServiceFactory creates DummyNlpService by default."""
        # Ensure SPARK_NLP_ENABLED is not set or false
        os.environ.pop("SPARK_NLP_ENABLED", None)
        
        service = NlpServiceFactory.create_nlp_service()
        assert isinstance(service, DummyNlpService)
    
    def test_nlp_factory_with_spark_enabled(self):
        """Test NlpServiceFactory with SPARK_NLP_ENABLED=true."""
        os.environ["SPARK_NLP_ENABLED"] = "true"
        
        service = NlpServiceFactory.create_nlp_service()
        
        # Should create SparkNlpService if requested, but fall back to Dummy if not available
        assert isinstance(service, (SparkNlpService, DummyNlpService))
        
        # Clean up
        os.environ.pop("SPARK_NLP_ENABLED", None)
    
    def test_get_nlp_service_singleton(self):
        """Test that get_nlp_service returns the same instance."""
        service1 = get_nlp_service()
        service2 = get_nlp_service()
        
        assert service1 is service2
    
    def test_analysis_context_enrichment(self):
        """Test that AnalysisContext can be enriched properly."""
        context = AnalysisContext(
            text="Sample text for analysis",
            schema_id="test_schema",
            session_id="session-123"
        )
        
        service = DummyNlpService()
        service.enrich(context)
        
        # Original fields should be preserved
        assert context.text == "Sample text for analysis"
        assert context.schema_id == "test_schema"
        assert context.session_id == "session-123"
        
        # NLP fields should be populated
        assert context.tokens is not None
        assert context.sentences is not None
        
        # Other fields should remain as defaults
        assert context.detected_markers == []
        assert context.confidence_scores == {}


@pytest.fixture(autouse=True)
def reset_nlp_service():
    """Reset the NLP service singleton between tests."""
    import app.services.nlp_service
    app.services.nlp_service._nlp_service_instance = None
    yield
    app.services.nlp_service._nlp_service_instance = None