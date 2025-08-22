#!/bin/bash

# Memorial Website - Development Server Startup Script

echo "Starting Memorial Website Development Server..."
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt 2>/dev/null || pip install -q fastapi uvicorn python-multipart jinja2 pydantic pydantic-settings email-validator itsdangerous 'passlib[bcrypt]' slowapi structlog sqlalchemy asyncpg

echo ""
echo "Configuration:"
echo "  Environment: Development"
echo "  Debug Mode: Enabled"
echo "  Port: 8000"
echo "  Host: 0.0.0.0"
echo ""
echo "Available endpoints:"
echo "  Main page:     http://localhost:8000/"
echo "  Health check:  http://localhost:8000/health"
echo "  API info:      http://localhost:8000/api/v1/info"
echo "  API docs:      http://localhost:8000/docs"
echo "  ReDoc:         http://localhost:8000/redoc"
echo ""
echo "Starting server..."
echo "Press Ctrl+C to stop the server"
echo "=============================================="

# Start the development server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload