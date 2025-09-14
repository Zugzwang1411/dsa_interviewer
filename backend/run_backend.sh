#!/bin/bash
export APP_ENV=development
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI application with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
