# Dockerfile for HiveMemory Dashboard Backend (ME_CORE_Backend_mar_spar)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PATH="/home/appuser/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN adduser --disabled-password --gecos '' appuser

# Copy requirements first for better caching
COPY requirements.txt .
RUN chown appuser:appuser requirements.txt

# Switch to non-root user for pip install
USER appuser

# Install Python dependencies
RUN pip install --user --no-cache-dir --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt

# Switch back to root to copy files
USER root

# Copy application code
COPY . .
RUN chown -R appuser:appuser /app

# Switch back to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Start application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]