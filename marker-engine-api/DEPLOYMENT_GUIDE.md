# MarkerEngine v1.0 - Spark NLP Deployment Guide

## Overview

This guide covers the deployment of MarkerEngine with full Spark NLP support, including both basic and advanced configurations.

## Prerequisites

- Docker and Docker Compose installed
- MongoDB Atlas connection string
- At least 8GB RAM for Spark NLP deployment
- Java 8 or 11 (for local development)
- Python 3.10+

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd marker-engine-api

# Create .env file from example
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
```env
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB_NAME=marker_engine
MOONSHOT_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here  # Optional fallback
```

### 2. Deploy Without Spark NLP (Lightweight)

```bash
# Build and run base version
docker-compose up markerengine-base

# API will be available at http://localhost:8000
```

### 3. Deploy With Spark NLP (Full Features)

```bash
# Build and run Spark version
docker-compose up markerengine-spark

# API will be available at http://localhost:8001
```

### 4. Deploy Both Versions

```bash
# Run both for comparison
docker-compose up

# Base API: http://localhost:8000
# Spark API: http://localhost:8001
```

## Local Development

### Without Spark NLP

```bash
# Install base dependencies
pip install -r requirements-base.txt

# Set environment
export SPARK_NLP_ENABLED=false

# Run locally
uvicorn app.main:app --reload
```

### With Spark NLP

```bash
# Install Java (macOS)
brew install openjdk@11

# Install all dependencies
pip install -r requirements-spark.txt

# Set environment
export SPARK_NLP_ENABLED=true
export JAVA_HOME=$(/usr/libexec/java_home -v 11)

# Run locally
uvicorn app.main:app --reload
```

## API Usage Examples

### Basic Analysis (v1 - Backward Compatible)

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ich vermisse dich, aber ich brauche Zeit für mich.",
    "schema_id": "relationship_markers"
  }'
```

### Enhanced Analysis with NLP (v2)

```bash
curl -X POST http://localhost:8001/analyze/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ich liebe dich, aber ich kann dir nicht mehr vertrauen.",
    "schema_id": "relationship_markers"
  }'
```

### Check Service Status

```bash
curl http://localhost:8001/analyze/v2/status
```

Response:
```json
{
  "orchestration_service": "active",
  "nlp_service": {
    "type": "SparkNlpServiceImpl",
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

### Batch Processing

```bash
curl -X POST http://localhost:8001/analyze/v2/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Ich liebe dich.",
      "Ich vermisse dich, aber ich brauche Abstand.",
      "Wir sollten darüber reden."
    ],
    "schema_id": "relationship_markers"
  }'
```

## Performance Tuning

### Spark Memory Configuration

Edit `docker-compose.yml`:

```yaml
environment:
  - SPARK_DRIVER_MEMORY=6g  # Increase for larger texts
  - SPARK_EXECUTOR_MEMORY=4g
  - SPARK_DRIVER_MAXRESULTSIZE=2g
```

### JVM Options

For local development:
```bash
export JAVA_OPTS="-Xmx4g -XX:+UseG1GC"
```

### Model Caching

Pre-download models during Docker build:

```dockerfile
# In Dockerfile, uncomment:
RUN python -c "import sparknlp; sparknlp.start(); \
    from sparknlp.pretrained import PretrainedPipeline; \
    PretrainedPipeline.downloadModels('de')"
```

## Monitoring

### Enable Monitoring Stack

```bash
# Start with monitoring
docker-compose --profile monitoring up

# Access:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Custom Metrics

The API exposes metrics at `/metrics`:

```bash
curl http://localhost:8001/metrics
```

Key metrics:
- `markerengine_requests_total` - Total API requests
- `markerengine_request_duration_seconds` - Request latency
- `markerengine_nlp_enrichment_duration_seconds` - NLP processing time
- `markerengine_markers_detected_total` - Total markers found

## Production Deployment

### Using Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: markerengine-spark
spec:
  replicas: 3
  selector:
    matchLabels:
      app: markerengine
  template:
    metadata:
      labels:
        app: markerengine
    spec:
      containers:
      - name: markerengine
        image: markerengine:spark-latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        env:
        - name: SPARK_NLP_ENABLED
          value: "true"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: markerengine-secrets
              key: database-url
```

### Using AWS ECS

```json
{
  "family": "markerengine-spark",
  "taskDefinition": {
    "containerDefinitions": [{
      "name": "markerengine",
      "image": "markerengine:spark-latest",
      "memory": 8192,
      "cpu": 4096,
      "environment": [
        {"name": "SPARK_NLP_ENABLED", "value": "true"},
        {"name": "SPARK_DRIVER_MEMORY", "value": "6g"}
      ]
    }]
  }
}
```

## Troubleshooting

### Common Issues

1. **Java Not Found**
   ```bash
   # Check Java installation
   java -version
   
   # Set JAVA_HOME
   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
   ```

2. **Out of Memory**
   ```bash
   # Increase Docker memory limit
   docker run -m 8g markerengine:spark
   
   # Or in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 8g
   ```

3. **Slow First Request**
   - First request loads NLP models (~30-60s)
   - Subsequent requests are fast (~200-500ms)
   - Consider model pre-loading in production

4. **Models Not Loading**
   ```python
   # Check model availability
   python -c "import sparknlp; print(sparknlp.version())"
   
   # Download models manually
   python -c "from sparknlp.pretrained import PretrainedPipeline; \
              PretrainedPipeline.download('explain_document_lg', 'de')"
   ```

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --log-level debug
```

Check Spark UI (local development):
- http://localhost:4040 (when Spark job is running)

## Performance Benchmarks

### Without NLP (Base)
- Startup time: ~2s
- First request: ~100ms
- Subsequent requests: ~50-100ms
- Memory usage: ~200MB

### With NLP (Spark)
- Startup time: ~10s
- First request: ~30-60s (model loading)
- Subsequent requests: ~200-500ms
- Memory usage: ~2-4GB

### Throughput
- Base version: ~100 req/s
- Spark version: ~10-20 req/s

## Security Considerations

1. **API Authentication**
   - Implement API key authentication
   - Use rate limiting
   - Enable CORS appropriately

2. **Database Security**
   - Use connection string with TLS
   - Implement IP whitelisting
   - Regular backups

3. **Container Security**
   - Run as non-root user
   - Scan images for vulnerabilities
   - Keep base images updated

## Backup and Recovery

### Database Backup
```bash
# Backup MongoDB
mongodump --uri="$DATABASE_URL" --out=backup/

# Restore
mongorestore --uri="$DATABASE_URL" backup/
```

### Application State
- Models are stateless (downloaded on demand)
- Only database contains persistent state
- Cache can be safely cleared

## Scaling Strategies

1. **Horizontal Scaling**
   - Deploy multiple API instances
   - Use load balancer (nginx, HAProxy)
   - Share Spark resources with cluster mode

2. **Vertical Scaling**
   - Increase memory for larger texts
   - More CPU cores for parallel processing
   - SSD storage for faster model loading

3. **Caching**
   - Implement Redis for marker results
   - Cache NLP annotations
   - Use CDN for static resources

## Future Enhancements

1. **GPU Support**
   - Use GPU-enabled Spark NLP models
   - Faster inference with CUDA
   - Batch processing optimization

2. **Multi-language Support**
   - Add English, Spanish models
   - Language detection
   - Cross-lingual markers

3. **Real-time Processing**
   - WebSocket support
   - Streaming text analysis
   - Live collaboration features

## Support

- Documentation: `/docs` (FastAPI automatic docs)
- Issues: GitHub Issues
- Monitoring: Check `/health` and `/metrics`

For production support, ensure you have:
- Monitoring alerts configured
- Backup procedures in place
- Scaling policies defined
- Security updates automated