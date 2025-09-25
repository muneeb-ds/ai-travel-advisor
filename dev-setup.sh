#!/bin/bash

# Development setup script for AI Travel Advisor

echo "🚀 Setting up AI Travel Advisor for development..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

# Create directories if they don't exist
mkdir -p backend/app/logs
mkdir -p frontend/logs

echo "✅ Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Start services:"
echo "   - Backend: cd backend && uv run uvicorn app.main:app --reload"
echo "   - Frontend: cd frontend && uv run streamlit run main.py"
echo "   - Or use Docker: docker-compose up"
echo ""
echo "Access the application at:"
echo "- Frontend: http://localhost:8501"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
