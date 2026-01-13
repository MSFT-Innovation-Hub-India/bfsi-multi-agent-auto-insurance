#!/bin/bash
# Azure App Service startup script for Batch API Server
# This script starts the batch processing FastAPI application

echo "Starting Vehicle Insurance Claims Processing API (Batch Mode)..."
echo "Port: $PORT"
echo "Python version: $(python --version)"

# Start the application with gunicorn (production-ready WSGI server)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
