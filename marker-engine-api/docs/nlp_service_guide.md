# NLP Service Abstraction Guide

## Overview

The NLP service abstraction provides a pluggable architecture for natural language processing capabilities in MarkerEngine. It allows the system to work with different NLP backends while maintaining a consistent interface.

## Architecture

### Core Components

1. **`NlpService` (Abstract Base Class)**
   - Defines the interface all NLP services must implement
   - Key method: `enrich(context: AnalysisContext) -> None`
   - Works in-place on the AnalysisContext object

2. **`DummyNlpService`**
   - No-op implementation for initial deployment
   - Performs basic whitespace tokenization
   - Always available (no external dependencies)

3. **`SparkNlpService`**
   - Stub for future Spark NLP integration
   - Will provide advanced NLP features when implemented
   - Falls back to basic processing if Spark NLP is unavailable

4. **`NlpServiceFactory`**
   - Creates the appropriate NLP service based on configuration
   - Uses `SPARK_NLP_ENABLED` environment variable

5. **`AnalysisContext`**
   - Central data structure that flows through the processing pipeline
   - Enriched in-place by NLP services
   - Contains both input data and NLP annotations

## Usage

### Basic Example

```python
from app.models.analysis_context import AnalysisContext
from app.services.nlp_service import get_nlp_service

# Create context
context = AnalysisContext(
    text="Ich vermisse dich, aber ich brauche Abstand.",
    schema_id="relationship_markers"
)

# Get NLP service (singleton)
nlp_service = get_nlp_service()

# Enrich context with NLP annotations
nlp_service.enrich(context)

# Context now contains tokens, sentences, etc.
print(f"Tokens: {context.tokens}")
print(f"Service used: {context.metadata['nlp_service']}")
```

### Configuration

Set the `SPARK_NLP_ENABLED` environment variable to control which service is used:

```bash
# Use dummy service (default)
export SPARK_NLP_ENABLED=false

# Use Spark NLP service (when available)
export SPARK_NLP_ENABLED=true
```

### Integration with Analyze Service

The analyze service can be updated to use NLP enrichment:

```python
from app.services.analyze_service_v2 import run_analysis_with_nlp

result = await run_analysis_with_nlp(
    text="Your text here",
    schema_id="schema_id",
    session_id="optional_session_id"
)
```

## AnalysisContext Structure

The `AnalysisContext` contains:

- **Input fields:**
  - `text`: The input text to analyze
  - `schema_id`: Schema identifier for filtering
  - `session_id`: Optional session tracking

- **NLP enrichments (populated by services):**
  - `tokens`: List of tokens
  - `sentences`: List of sentences
  - `pos_tags`: Part-of-speech tags
  - `named_entities`: Named entities
  - `dependency_parse`: Dependency parse tree
  - `embeddings`: Word/sentence embeddings

- **Results:**
  - `detected_markers`: Markers found in the text
  - `confidence_scores`: Confidence scores for detections
  - `metadata`: Additional service-specific metadata

## Extending the System

### Adding a New NLP Service

1. Create a new class inheriting from `NlpService`:

```python
class MyCustomNlpService(NlpService):
    def enrich(self, context: AnalysisContext) -> None:
        # Your NLP processing logic here
        context.tokens = self._tokenize(context.text)
        context.metadata["nlp_service"] = "my_custom"
    
    def is_available(self) -> bool:
        # Check if your service dependencies are available
        return self._check_dependencies()
```

2. Update the factory to support your service:

```python
if os.getenv("USE_CUSTOM_NLP") == "true":
    return MyCustomNlpService()
```

### Writing NLP-Aware Detectors

Detectors can use the enriched context:

```python
def detect_with_context(context: AnalysisContext):
    """Enhanced detection using NLP features."""
    if not context.tokens:
        return None
    
    # Use NLP features for better detection
    for i, token in enumerate(context.tokens):
        if token.lower() == "aber" and i > 0:
            # Found conjunction, check context
            return {
                "confidence": 0.85,
                "details": {
                    "trigger_token": token,
                    "position": i
                }
            }
    
    return None
```

## Benefits

1. **Parallel Development**: Base system works without heavy NLP dependencies
2. **Pluggable Architecture**: Easy to swap NLP backends
3. **Progressive Enhancement**: Start simple, add advanced features later
4. **Testing**: Easy to test with dummy implementation
5. **Performance**: Can optimize different implementations independently

## Future Enhancements

When implementing `SparkNlpService`:

1. Add Spark NLP pipeline configuration
2. Implement model loading and caching
3. Add support for multiple languages
4. Include custom models for domain-specific tasks
5. Add streaming support for real-time processing

## Testing

Run the NLP service tests:

```bash
pytest tests/test_nlp_service.py -v
```

The tests cover:
- Basic tokenization with DummyNlpService
- Factory pattern behavior
- Singleton pattern for service instances
- Context enrichment
- Fallback behavior when services are unavailable