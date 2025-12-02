#!/bin/bash

# Databricks PS AI Workflow Inspector - Startup Script

echo "=================================================="
echo "   Databricks PS AI Workflow Inspector"
echo "=================================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found."
    exit 1
fi

# Check for Databricks CLI
if ! command -v databricks &> /dev/null; then
    echo "Warning: 'databricks' CLI not found. Backend may fail to fetch jobs."
    echo "Please install it: https://docs.databricks.com/dev-tools/cli/index.html"
fi

# Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install Dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt > /dev/null

# Create Output Directories
mkdir -p outputs/reports
mkdir -p outputs/logs

# Start Backend
echo "Starting Backend Server..."
echo "Access the UI at: http://localhost:8000"
echo "Press Ctrl+C to stop."

# Run uvicorn from the root, pointing to backend.app:app
# We need to set PYTHONPATH so it finds backend modules
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
