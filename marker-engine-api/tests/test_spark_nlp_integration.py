"""
Integration tests for Spark NLP functionality in MarkerEngine.
Tests the complete pipeline from API to NLP processing.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.models.analysis_context import AnalysisContext
from app.services.spark_nlp_service import SparkNlpServiceImpl
from app.services.activation_rules_engine import ActivationRulesEngine
from app.services.orchestration_service import OrchestrationService
from app.models.marker import Marker, Frame


class TestSparkNlpIntegration:
    """Integration tests for Spark NLP pipeline"""
    
    @pytest.fixture
    def mock_spark_available(self):
        """Mock Spark NLP as available"""
        with patch('app.services.spark_nlp_service.sparknlp'):
            with patch('app.services.spark_nlp_service.SparkSession'):
                yield
    
    def test_spark_nlp_initialization(self, mock_spark_available):
        """Test Spark NLP service initialization"""
        service = SparkNlpServiceImpl()
        
        # Should initialize successfully with mocks
        assert service.is_available()
        assert service.get_model_info()['available']
    
    def test_basic_text_enrichment(self, mock_spark_available):
        """Test basic text enrichment with NLP"""
        service = SparkNlpServiceImpl()
        context = AnalysisContext(
            text="Ich liebe dich, aber ich brauche Zeit für mich."
        )
        
        # Mock the pipeline execution
        with patch.object(service, '_pipeline') as mock_pipeline:
            mock_result = Mock()
            mock_result.collect.return_value = [{
                'token_array': ["Ich", "liebe", "dich", ",", "aber", "ich", "brauche", "Zeit", "für", "mich", "."],
                'pos_array': ["PRON", "VERB", "PRON", "PUNCT", "CONJ", "PRON", "VERB", "NOUN", "ADP", "PRON", "PUNCT"],
                'sentence': [Mock(result="Ich liebe dich, aber ich brauche Zeit für mich.")],
                'lemma_array': ["ich", "lieben", "du", ",", "aber", "ich", "brauchen", "Zeit", "für", "ich", "."],
                'clean_tokens_array': ["liebe", "brauche", "Zeit"],
                'ner_array': ["O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O"],
                'sentiment_array': ["neutral", "positive", "neutral", "neutral", "neutral", "neutral", "negative", "neutral", "neutral", "neutral", "neutral"]
            }]
            
            mock_pipeline.fit.return_value.transform.return_value = mock_result
            
            # Enrich context
            service.enrich(context)
        
        # Verify enrichment
        assert context.tokens == ["Ich", "liebe", "dich", ",", "aber", "ich", "brauche", "Zeit", "für", "mich", "."]
        assert len(context.pos_tags) == 11
        assert context.pos_tags[1]['pos'] == "VERB"
        assert len(context.lemmas) == 11
        assert context.sentences == ["Ich liebe dich, aber ich brauche Zeit für mich."]
        assert context.clean_tokens == ["liebe", "brauche", "Zeit"]
        assert 'positive' in context.sentiment_scores
    
    def test_named_entity_grouping(self, mock_spark_available):
        """Test named entity recognition and grouping"""
        service = SparkNlpServiceImpl()
        
        # Test with entities
        tokens = ["Angela", "Merkel", "trifft", "Joe", "Biden", "in", "Berlin", "."]
        ner_tags = ["B-PER", "I-PER", "O", "B-PER", "I-PER", "O", "B-LOC", "O"]
        
        entities = service._group_entities(tokens, ner_tags)
        
        assert len(entities) == 3
        assert entities[0]['text'] == "Angela Merkel"
        assert entities[0]['entity'] == "PER"
        assert entities[1]['text'] == "Joe Biden"
        assert entities[2]['text'] == "Berlin"
        assert entities[2]['entity'] == "LOC"
    
    def test_sentiment_calculation(self, mock_spark_available):
        """Test sentiment score calculation"""
        service = SparkNlpServiceImpl()
        
        sentiments = ["positive", "positive", "neutral", "negative", "positive"]
        scores = service._calculate_sentiment_scores(sentiments)
        
        assert scores['positive'] == 0.6  # 3/5
        assert scores['negative'] == 0.2  # 1/5
        assert scores['neutral'] == 0.2   # 1/5
    
    def test_fallback_on_error(self, mock_spark_available):
        """Test fallback processing when Spark fails"""
        service = SparkNlpServiceImpl()
        context = AnalysisContext(text="Test text")
        
        # Mock pipeline to raise error
        with patch.object(service, '_pipeline') as mock_pipeline:
            mock_pipeline.fit.side_effect = Exception("Spark error")
            
            service.enrich(context)
        
        # Should fall back to basic processing
        assert context.tokens == ["Test", "text"]
        assert context.sentences == ["Test text"]
        assert context.metadata['nlp_service'] == "spark_nlp_fallback"
        assert 'error' in context.metadata


class TestActivationRulesEngine:
    """Test advanced activation rules"""
    
    @pytest.fixture
    def rules_engine(self):
        return ActivationRulesEngine()
    
    @pytest.fixture
    def sample_context(self):
        context = AnalysisContext(text="Ich liebe dich, aber ich brauche Abstand.")
        context.tokens = ["Ich", "liebe", "dich", ",", "aber", "ich", "brauche", "Abstand", "."]
        context.pos_tags = [
            {"token": "Ich", "pos": "PRON"},
            {"token": "liebe", "pos": "VERB"},
            {"token": "dich", "pos": "PRON"},
            {"token": ",", "pos": "PUNCT"},
            {"token": "aber", "pos": "CONJ"},
            {"token": "ich", "pos": "PRON"},
            {"token": "brauche", "pos": "VERB"},
            {"token": "Abstand", "pos": "NOUN"},
            {"token": ".", "pos": "PUNCT"}
        ]
        context.sentiment_scores = {
            "positive": 0.3,
            "negative": 0.5,
            "neutral": 0.2
        }
        context.detected_markers = [
            {"marker_id": "S_LOVE", "examples_matched": ["liebe"]},
            {"marker_id": "S_NEED_SPACE", "examples_matched": ["brauche Abstand"]}
        ]
        return context
    
    def test_temporal_rule(self, rules_engine, sample_context):
        """Test temporal sequence rule"""
        marker = Marker(
            id="C_AMBIVALENCE_TEMPORAL",
            frame=Frame(signal="ambivalence", concept="mixed feelings", pragmatics="", narrative=""),
            examples=[],
            composed_of=["S_LOVE", "S_NEED_SPACE"],
            activation={
                "type": "TEMPORAL",
                "window": 10,
                "strict_order": True
            }
        )
        
        detected_ids = {"S_LOVE", "S_NEED_SPACE"}
        
        result = rules_engine.check_activation(marker, sample_context, detected_ids)
        
        # Should be activated as components appear in order within window
        assert result['activated']
        assert result['confidence'] > 0.6
        assert result['nlp_enhanced']
        assert 'temporal_pattern' in result['details']
    
    def test_sentiment_rule(self, rules_engine, sample_context):
        """Test sentiment alignment rule"""
        marker = Marker(
            id="C_EMOTIONAL_CONFLICT",
            frame=Frame(signal="conflict", concept="emotional", pragmatics="", narrative=""),
            examples=[],
            composed_of=["S_LOVE", "S_NEED_SPACE"],
            activation={
                "type": "SENTIMENT",
                "alignment": "contrasting",
                "min_confidence": 0.3
            }
        )
        
        detected_ids = {"S_LOVE", "S_NEED_SPACE"}
        
        # Mock component sentiments
        with patch.object(rules_engine, '_get_component_sentiments') as mock_sentiments:
            mock_sentiments.return_value = {
                "S_LOVE": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
                "S_NEED_SPACE": {"positive": 0.1, "negative": 0.7, "neutral": 0.2}
            }
            
            result = rules_engine.check_activation(marker, sample_context, detected_ids)
        
        # Should be activated due to contrasting sentiments
        assert result['activated']
        assert result['confidence'] > 0.5
        assert result['details']['sentiment_alignment'] == 'contrasting'
    
    def test_proximity_rule(self, rules_engine, sample_context):
        """Test proximity-based activation"""
        marker = Marker(
            id="C_CLOSE_RELATION",
            frame=Frame(signal="relation", concept="close", pragmatics="", narrative=""),
            examples=[],
            composed_of=["S_LOVE", "S_NEED_SPACE"],
            activation={
                "type": "PROXIMITY",
                "max_distance": 5
            }
        )
        
        detected_ids = {"S_LOVE", "S_NEED_SPACE"}
        
        # Mock component positions
        with patch.object(rules_engine, '_find_component_positions') as mock_positions:
            mock_positions.return_value = {
                "S_LOVE": [1],  # "liebe" at position 1
                "S_NEED_SPACE": [6]  # "brauche" at position 6
            }
            
            result = rules_engine.check_activation(marker, sample_context, detected_ids)
        
        # Should be activated as distance is 5 tokens
        assert result['activated']
        assert result['details']['actual_max_distance'] == 5
    
    def test_negation_rule(self, rules_engine):
        """Test negation detection rule"""
        context = AnalysisContext(text="Ich liebe dich nicht mehr.")
        context.tokens = ["Ich", "liebe", "dich", "nicht", "mehr", "."]
        context.detected_markers = [
            {"marker_id": "S_LOVE", "examples_matched": ["liebe"]}
        ]
        
        marker = Marker(
            id="C_LOVE_NEGATED",
            frame=Frame(signal="negated love", concept="absence", pragmatics="", narrative=""),
            examples=[],
            composed_of=["S_LOVE"],
            activation={
                "type": "NEGATION",
                "allow_negation": True,
                "negation_window": 3
            }
        )
        
        detected_ids = {"S_LOVE"}
        
        # Mock component positions
        with patch.object(rules_engine, '_find_component_positions') as mock_positions:
            mock_positions.return_value = {"S_LOVE": [1]}
            
            result = rules_engine.check_activation(marker, context, detected_ids)
        
        # Should be activated with negation detected
        assert result['activated']
        assert result['details']['negation_detected']
    
    def test_composite_rule(self, rules_engine, sample_context):
        """Test composite rule with multiple conditions"""
        marker = Marker(
            id="C_COMPLEX_AMBIVALENCE",
            frame=Frame(signal="complex", concept="ambivalence", pragmatics="", narrative=""),
            examples=[],
            composed_of=["S_LOVE", "S_NEED_SPACE"],
            activation={
                "type": "COMPOSITE",
                "operator": "AND",
                "rules": [
                    {"type": "ANY", "count": 1},
                    {"type": "TEMPORAL", "window": 15},
                    {"type": "SENTIMENT", "alignment": "contrasting"}
                ]
            }
        )
        
        detected_ids = {"S_LOVE", "S_NEED_SPACE"}
        
        # Mock necessary methods
        with patch.object(rules_engine, '_find_component_positions') as mock_pos:
            with patch.object(rules_engine, '_get_component_sentiments') as mock_sent:
                mock_pos.return_value = {"S_LOVE": [1], "S_NEED_SPACE": [6]}
                mock_sent.return_value = {
                    "S_LOVE": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
                    "S_NEED_SPACE": {"positive": 0.1, "negative": 0.7, "neutral": 0.2}
                }
                
                result = rules_engine.check_activation(marker, sample_context, detected_ids)
        
        # Should be activated as all sub-rules pass
        assert result['activated']
        assert result['rule_type'] == 'COMPOSITE'
        assert len(result['details']['rule_results']) == 3


@pytest.mark.asyncio
class TestFullPipeline:
    """Test the complete pipeline from API to results"""
    
    async def test_orchestration_with_nlp(self):
        """Test full orchestration with NLP enabled"""
        # This would require a full integration environment
        # For now, we test the orchestration flow with mocks
        
        with patch('app.services.orchestration_service.MarkerService') as mock_marker:
            with patch('app.services.orchestration_service.get_nlp_service') as mock_nlp:
                # Setup mocks
                marker_service = Mock()
                nlp_service = Mock()
                
                mock_marker.return_value = marker_service
                mock_nlp.return_value = nlp_service
                
                nlp_service.is_available.return_value = True
                nlp_service.enrich = Mock()
                
                marker_service.initial_scan.return_value = [
                    {"marker_id": "S_LOVE", "confidence": 0.8}
                ]
                marker_service.contextual_rescan.return_value = [
                    {"marker_id": "C_AMBIVALENCE", "confidence": 0.9}
                ]
                
                # Create service and run analysis
                from app.services.orchestration_service import OrchestrationService
                service = OrchestrationService()
                
                result = await service.analyze(
                    text="Ich liebe dich, aber ich brauche Abstand.",
                    schema_id="relationship"
                )
                
                # Verify all phases were executed
                assert result['status'] == 'success'
                assert result['nlp_enriched']
                assert len(result['markers']) == 2
                assert 'phase1_initial_scan' in result['performance_metrics']
                assert 'phase2_nlp_enrichment' in result['performance_metrics']
                assert 'phase3_contextual_rescan' in result['performance_metrics']
    
    async def test_batch_processing(self):
        """Test batch text processing"""
        with patch('app.services.orchestration_service.MarkerService'):
            with patch('app.services.orchestration_service.get_nlp_service'):
                from app.services.orchestration_service import OrchestrationService
                service = OrchestrationService()
                
                texts = [
                    "Ich liebe dich.",
                    "Ich vermisse dich, aber ich brauche Zeit.",
                    "Wir sollten reden."
                ]
                
                results = await service.analyze_batch(texts, schema_id="test")
                
                assert len(results) == 3
                for i, result in enumerate(results):
                    assert result['text'] == texts[i]
                    assert result['status'] in ['success', 'error']