# AI Travel Advisor

A full-stack travel advisory application that combines personal knowledge management with AI-powered insights and real-time weather data.

## Features

### Core Functionality
- **Destination Management**: Add, view, edit, and delete travel destinations
- **Knowledge Base**: Store and manage personal notes and information about destinations
- **AI Q&A**: Ask questions and get intelligent responses combining your knowledge with real-time data
- **Weather Integration**: Get current weather information for any destination
- **RAG (Retrieval-Augmented Generation)**: AI responses use your personal knowledge base for context

### Key Capabilities
- Context-aware AI responses based on your stored knowledge
- Real-time weather data integration using Open-Meteo API
- Responsive web interface built with Streamlit
- RESTful API backend with FastAPI
- PostgreSQL database with SQLAlchemy ORM
- Docker containerization for easy deployment

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: Python SQL toolkit and ORM
- **LangChain**: Framework for developing applications with LLMs
- **OpenAI GPT**: Language model for AI responses
- **ChromaDB**: Vector database for RAG functionality

### Frontend
- **Streamlit**: Python web framework for data applications
- **Requests**: HTTP library for API communication

### Infrastructure
- **Docker & Docker Compose**: Containerization and orchestration
- **uv**: Fast Python package manager
- **Python 3.11**: Programming language

## Project Structure

```
keyveve/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   │   ├── destinations.py
│   │   │   ├── knowledge_base.py
│   │   │   └── ai_chat.py
│   │   ├── core/              # Core configuration
│   │   │   └── database.py
│   │   ├── models/            # Database and Pydantic models
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   ├── services/          # Business logic layer
│   │   │   ├── destination_service.py
│   │   │   ├── knowledge_service.py
│   │   │   ├── ai_service.py
│   │   │   └── weather_service.py
│   │   └── main.py           # FastAPI application entry point
│   └── Dockerfile            # Backend container configuration
├── frontend/                  # Streamlit frontend application
│   ├── pages/                # Streamlit pages
│   │   ├── destinations.py
│   │   ├── knowledge_base.py
│   │   └── ai_chat.py
│   ├── utils/                # Utility modules
│   │   └── api_client.py
│   ├── main.py              # Main Streamlit application
│   └── Dockerfile           # Frontend container configuration
├── docker-compose.yml        # Multi-container application setup
├── pyproject.toml           # Python project configuration
├── env.example              # Environment variables template
└── README.md               # This file
```

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key (get one from [OpenAI](https://platform.openai.com/api-keys))

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd keyveve
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend (Streamlit): http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development Setup

If you prefer to run the application locally without Docker:

1. **Install uv (if not already installed)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Start PostgreSQL**
   ```bash
   docker run --name travel-postgres -e POSTGRES_DB=travel_advisor -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Start the backend**
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Start the frontend (in a new terminal)**
   ```bash
   cd frontend
   uv run streamlit run main.py --server.port 8501
   ```

## Environment Variables

### Required Variables
- `OPENAI_API_KEY`: Your OpenAI API key for AI functionality

### Optional Variables
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/travel_advisor`)
- `BACKEND_HOST`: Backend host (default: `localhost`)
- `BACKEND_PORT`: Backend port (default: `8000`)
- `FRONTEND_HOST`: Frontend host (default: `localhost`)
- `FRONTEND_PORT`: Frontend port (default: `8501`)

## Usage Guide

### 1. Managing Destinations

**Adding Destinations:**
1. Navigate to the "🏠 Destinations" page
2. Enter a destination name (e.g., "Paris", "Tokyo")
3. Click "Add Destination"

**Managing Destinations:**
- Edit destination names using the "📝 Edit" button
- Delete destinations with the "🗑️ Delete" button
- Search destinations using the search box

### 2. Building Your Knowledge Base

**Adding Knowledge:**
1. Go to the "📚 Knowledge Base" page
2. Select a destination from the dropdown
3. Add detailed information about the destination
4. Click "Add Knowledge Entry"

**Knowledge Examples:**
- Restaurant recommendations and local cuisine
- Tourist attractions and hidden gems
- Transportation tips and local customs
- Personal experiences and travel stories
- Cultural insights and historical information

### 3. AI-Powered Q&A

**Asking Questions:**
1. Visit the "🤖 AI Chat" page
2. Optionally select a destination for context
3. Type your question in the text area
4. Click "🚀 Send"

**Question Examples:**
- "What's the best museum to visit in Paris and how's the weather?"
- "Tell me about local cuisine in Tokyo"
- "What are some hidden gems in New York?"
- "How's the weather in London right now?"

**AI Capabilities:**
- Answers based on your personal knowledge base
- Real-time weather information when requested
- Context-aware responses for specific destinations
- Source attribution showing where information came from

## API Documentation

### Destinations Endpoints
- `GET /api/v1/destinations/` - List all destinations
- `POST /api/v1/destinations/` - Create a new destination
- `GET /api/v1/destinations/{id}` - Get destination by ID
- `PUT /api/v1/destinations/{id}` - Update destination
- `DELETE /api/v1/destinations/{id}` - Delete destination

### Knowledge Base Endpoints
- `GET /api/v1/knowledge/` - List knowledge entries
- `POST /api/v1/knowledge/` - Create knowledge entry
- `GET /api/v1/knowledge/{id}` - Get knowledge entry by ID
- `PUT /api/v1/knowledge/{id}` - Update knowledge entry
- `DELETE /api/v1/knowledge/{id}` - Delete knowledge entry

### AI Chat Endpoints
- `POST /api/v1/chat/` - Send chat message to AI
- `GET /api/v1/chat/destinations/{id}/context` - Get destination context

For detailed API documentation, visit http://localhost:8000/docs when the backend is running.

## Database Schema

### Destinations Table
- `id`: Primary key
- `name`: Destination name
- `created_at`: Creation timestamp

### Knowledge Base Table
- `id`: Primary key
- `destination_id`: Foreign key to destinations
- `content`: Knowledge content
- `created_at`: Creation timestamp

### Users Table (Optional)
- `id`: Primary key
- `username`: User name
- `email`: User email
- `created_at`: Creation timestamp

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run ruff format .
```

### Linting
```bash
uv run ruff check .
```

### Adding Dependencies
```bash
uv add package-name
```

## Troubleshooting

### Common Issues

**1. Docker containers won't start**
- Ensure Docker is running
- Check if ports 8000, 8501, and 5432 are available
- Run `docker-compose logs` to see error messages

**2. AI responses aren't working**
- Verify your OpenAI API key is correctly set in the `.env` file
- Check that you have sufficient credits in your OpenAI account
- Look at backend logs: `docker-compose logs backend`

**3. Database connection errors**
- Ensure PostgreSQL container is running
- Check database credentials in environment variables
- Wait for the database to be ready (health check in docker-compose)

**4. Frontend can't connect to backend**
- Verify backend is running on port 8000
- Check `BACKEND_URL` environment variable
- Ensure CORS is configured correctly

### Logs and Debugging

**View application logs:**
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

**Connect to database:**
```bash
docker-compose exec db psql -U postgres -d travel_advisor
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run linting and formatting
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the GPT language model
- Open-Meteo for weather data
- Streamlit for the frontend framework
- FastAPI for the backend framework
- LangChain for RAG implementation
