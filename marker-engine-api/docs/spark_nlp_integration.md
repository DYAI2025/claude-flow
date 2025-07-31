# Spark NLP Integration Architecture for MarkerEngine v1.0

## Overview

The Spark NLP integration enables advanced semantic reasoning capabilities in MarkerEngine through a sophisticated 3-phase analysis pipeline. This document describes the architecture, implementation details, and usage patterns.

## Architecture Components

### 1. AnalysisContext

The `AnalysisContext` serves as the central data structure that flows through all analysis phases:

```python
class AnalysisContext:
    request_id: str              # Unique identifier
    text: str                    # Input text
    tokens: List[str]            # Tokenized text
    sentences: List[str]         # Sentence boundaries
    pos_tags: List[Dict]         # Part-of-speech tags
    named_entities: List[Dict]   # Named entities
    dependency_parse: List[Dict] # Dependency relations
    detected_markers: List[Dict] # Found markers
    metadata: Dict[str, Any]     # Additional data
```

### 2. OrchestrationService

Manages the 3-phase analysis pipeline:

**Phase 1: Initial Scan**
- Fast pattern matching for atomic (A_) and signal (S_) markers
- Basic text search without NLP overhead
- Builds activation candidates for complex markers

**Phase 2: NLP Enrichment**
- Tokenization and sentence segmentation
- Part-of-speech tagging
- Named entity recognition
- Dependency parsing
- Sentiment analysis (future)

**Phase 3: Contextual Rescan**
- Activates composed (C_) and meta-markers (MM_)
- Uses NLP data for sophisticated reasoning
- Applies complex activation rules
- Adjusts confidence scores based on context

### 3. NLP Service Abstraction

Pluggable architecture supporting multiple backends:

```python
class NlpService(ABC):
    @abstractmethod
    def enrich(self, context: AnalysisContext) -> None:
        """Enrich context with NLP annotations"""
        pass
```

**Implementations:**
- `DummyNlpService`: Basic tokenization for initial deployment
- `SparkNlpService`: Full Spark NLP pipeline (when enabled)

### 4. Enhanced MarkerService

Split into two methods for phased processing:

- `initial_scan()`: Phase 1 detection
- `contextual_rescan()`: Phase 3 activation with NLP data

## Complex Activation Rules

The system supports sophisticated marker activation patterns:

### Rule Types

1. **ALL**: All components must be present
   ```json
   {"type": "ALL"}
   ```

2. **ANY**: At least one component must be present
   ```json
   {"type": "ANY"}
   ```

3. **ANY_N**: At least N components must be present
   ```json
   {"type": "ANY_N", "count": 2}
   ```

4. **TEMPORAL**: Components must appear in sequence (future)
   ```json
   {"type": "TEMPORAL", "window": 5}
   ```

### NLP-Enhanced Activation

The system adjusts activation confidence based on:

- **Proximity**: How close components are to each other
- **Negation**: Presence of negation words reduces confidence
- **Temporal markers**: Boost for temporal sequences
- **Sentiment alignment**: Components with matching sentiment (future)

## API Usage

### Basic Analysis

```bash
POST /analyze/v2
{
  "text": "Ich vermisse dich, aber ich brauche Abstand.",
  "schema_id": "relationship_markers"
}
```

### Response Structure

```json
{
  "request_id": "uuid",
  "status": "success",
  "markers": [...],
  "phases": {
    "phase1_initial_scan": {
      "markers_found": 5,
      "processing_time": 0.12
    },
    "phase2_nlp_enrichment": {
      "enrichment": {
        "tokens": 8,
        "sentences": 1
      },
      "processing_time": 0.05
    },
    "phase3_contextual_rescan": {
      "markers_added": 2,
      "processing_time": 0.08
    }
  },
  "nlp_enriched": true,
  "performance_metrics": {...}
}
```

## Deployment Options

### 1. Without Spark NLP (Default)

```bash
pip install -r requirements-base.txt
export SPARK_NLP_ENABLED=false
```

- Uses DummyNlpService
- Basic tokenization only
- All features work but with reduced accuracy

### 2. With Spark NLP

```bash
pip install -r requirements-spark.txt
export SPARK_NLP_ENABLED=true
```

- Full NLP pipeline
- Advanced semantic reasoning
- Higher resource requirements

## Performance Characteristics

### Without NLP
- Phase 1: ~50-100ms for typical text
- Phase 2: Skipped
- Phase 3: Minimal processing

### With NLP
- Phase 1: ~50-100ms (unchanged)
- Phase 2: ~200-500ms (NLP processing)
- Phase 3: ~100-200ms (enhanced detection)

## Future Enhancements

1. **Sentiment Analysis Integration**
   - Detect emotional valence changes
   - Adjust marker confidence based on sentiment

2. **Multi-language Support**
   - Language detection
   - Language-specific NLP models

3. **Custom NLP Models**
   - Domain-specific entity recognition
   - Specialized tokenization rules

4. **Streaming Support**
   - Real-time text analysis
   - Incremental marker detection

## Testing

### Unit Tests

```bash
pytest tests/test_orchestration_service.py -v
pytest tests/test_nlp_service.py -v
```

### Integration Tests

```bash
pytest tests/test_integration_pipeline.py -v
```

### Performance Tests

```bash
pytest tests/test_performance.py -v --benchmark
```

## Monitoring

The system provides detailed metrics for each phase:

```bash
GET /analyze/v2/status
```

Returns service availability and configuration:

```json
{
  "orchestration_service": "active",
  "nlp_service": {
    "type": "SparkNlpService",
    "available": true,
    "spark_nlp_enabled": true
  },
  "phases_enabled": {
    "phase1_initial_scan": true,
    "phase2_nlp_enrichment": true,
    "phase3_contextual_rescan": true
  }
}
```

## Troubleshooting

### Common Issues

1. **Spark NLP not loading**
   - Check Java installation (Java 8 or 11 required)
   - Verify Spark NLP dependencies: `pip show spark-nlp`

2. **Memory issues**
   - Increase Java heap: `export JAVA_OPTS="-Xmx4g"`
   - Use smaller NLP models initially

3. **Performance degradation**
   - Monitor phase timings in response
   - Consider disabling Phase 3 for simple queries

## Code Examples

### Custom Detector with NLP

```python
def detect_with_context(context: AnalysisContext):
    """Enhanced detection using NLP features"""
    
    if not context.tokens:
        return None
    
    # Use POS tags for better detection
    for i, (token, pos) in enumerate(zip(context.tokens, context.pos_tags)):
        if token.lower() == "aber" and pos.get("pos") == "CONJ":
            # Found conjunction with correct POS
            return {
                "confidence": 0.95,
                "details": {
                    "trigger": token,
                    "pos": pos,
                    "position": i
                }
            }
```

### Extending the System

```python
from app.services.nlp_service import NlpService

class CustomNlpService(NlpService):
    def enrich(self, context: AnalysisContext) -> None:
        # Your custom NLP logic here
        pass
    
    def is_available(self) -> bool:
        return True
```