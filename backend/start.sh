#!/bin/bash

# HiveMemory Dashboard Backend Startup Script

echo "Starting HiveMemory Dashboard Backend..."

# Create necessary directories
mkdir -p /mnt/memory
mkdir -p agents
mkdir -p logs

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the FastAPI application
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-config logging.yaml 2>&1 | tee logs/backend.log