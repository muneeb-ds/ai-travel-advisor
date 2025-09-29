# AI Travel Advisor

A sophisticated full-stack AI-powered travel planning application that combines personal knowledge management with intelligent itinerary generation. The system uses LangGraph agents to orchestrate multiple tools for comprehensive travel planning, including flights, lodging, events, weather, and personalized recommendations.

<img width="2137" height="1816" alt="mermaid-diagram-2025-09-30-041515" src="https://github.com/user-attachments/assets/446673b7-78f5-444b-b69a-08493bbf2145" />



## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-travel-advisor
   ```

2. **Generate SSL certificates for JWT authentication**
   ```bash
   cd backend
   mkdir -p certs && cd certs
   openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
   openssl rsa -pubout -in private_key.pem -out public_key.pem
   cd ../..
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key and other required variables.
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Build and run the application**
   ```bash
   # Build backend image
   cd backend
   docker build -t travel-advisor-backend .
   cd ..
   
   # Build frontend image
   cd frontend
   docker build -t travel-advisor-frontend .
   cd ..
   
   # Start all services
   docker compose up
   ```

5. **Access the application**
   - **Frontend**: http://localhost:8501
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

6. **Initial Login**
   - **Email**: admin@example.com
   - **Password**: admin

## 🌟 Key Features

- **AI Planning Engine**: LangGraph-powered multi-step planning with constraint validation and automatic repair
- **Comprehensive Tools**: Flight search, lodging, events, weather, transit, and currency exchange
- **Knowledge Base**: Personal travel insights with vector search and citation tracking
- **Enterprise Security**: JWT authentication, multi-tenancy, rate limiting, and Redis caching

## 🏗️ Architecture

- **Backend**: FastAPI with PostgreSQL + pgvector, LangGraph agents, Redis caching
- **Frontend**: Streamlit with multi-page interface and real-time chat
- **Infrastructure**: Docker Compose with health checks and volume mounting


## 📖 Usage

### Core Workflow
1. **Setup**: Create account (auto-creates organization)
2. **Destinations**: Add places you want to visit
3. **Knowledge Base**: Store travel insights and upload documents
4. **AI Planning**: Request itineraries with natural language

### Example Requests
```
"Plan a 5-day trip to Tokyo with a budget of $2000, focusing on traditional culture"
"Create a family-friendly Paris itinerary for 7 days in December"
"Plan a weekend getaway to Barcelona with restaurant recommendations"
```

### AI Planning Process
1. Constraint extraction → 2. Plan generation → 3. Tool orchestration → 4. Validation → 5. Repair → 6. Synthesis

### Response Format
- **Markdown itinerary** with day-by-day breakdown
- **Citations** for all recommendations
- **Tools used** and decision reasoning
- **Cost estimates** and timing details

## 🛠️ Development

### Local Setup
```bash
# Install dependencies
cd backend && uv sync
cd ../frontend && uv sync

# Start services
docker compose up db redis -d
cd backend && alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
cd frontend && streamlit run app.py --server.port 8501
```

### Key API Endpoints
- **Auth**: `/api/v1/auth/*` (signup, login, refresh, logout)
- **Destinations**: `/api/v1/destinations/*` (CRUD operations)
- **Knowledge**: `/api/v1/knowledge/*` (CRUD operations)
- **Planning**: `/api/v1/qa/plan` (generate itineraries)


## 🚨 Troubleshooting

### Common Issues
- **Certificates**: Ensure `backend/certs/private_key.pem` and `public_key.pem` exist
- **Database**: Check with `docker compose ps db` and `docker compose logs db`
- **OpenAI**: Verify API key in `.env` and sufficient credits
- **Frontend**: Ensure backend runs on port 8000

### Debug Commands
```bash
docker compose logs                    # All services
docker compose exec db psql -U travel-advisor -d travel-advisor
docker compose exec redis redis-cli
```

**Happy Travel Planning! ✈️**
