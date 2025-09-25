# Architecture Overview

## Layered Architecture Pattern

The AI Travel Advisor backend has been refactored to follow a clean **Repository-Service-Controller** pattern with clear separation of concerns:

```
┌─────────────────┐
│   Controllers   │  ← API Layer (app/api/)
│   (FastAPI)     │
└─────────┬───────┘
          │
┌─────────▼───────┐
│    Services     │  ← Business Logic Layer (app/services/)
│  (Domain Logic) │
└─────────┬───────┘
          │
┌─────────▼───────┐
│  Repositories   │  ← Data Access Layer (app/repositories/)
│ (Data Access)   │
└─────────┬───────┘
          │
┌─────────▼───────┐
│    Database     │  ← PostgreSQL
│   (PostgreSQL)  │
└─────────────────┘
```

## Layer Responsibilities

### 1. Controller Layer (`app/api/`)
**Purpose**: Handle HTTP requests/responses and routing
- Validate input parameters
- Call appropriate service methods
- Handle exceptions from service layer
- Return proper HTTP status codes and responses
- **Only imports from**: Service layer

**Files**:
- `destinations.py` - Destination management endpoints
- `knowledge_base.py` - Knowledge base management endpoints
- `ai_chat.py` - AI chat functionality endpoints

### 2. Service Layer (`app/services/`)
**Purpose**: Implement business logic and orchestrate operations
- Validate business rules
- Coordinate between multiple repositories
- Handle domain-specific logic
- Throw meaningful exceptions
- **Only imports from**: Repository layer, external services, schemas

**Files**:
- `destination_service.py` - Destination business logic
- `knowledge_service.py` - Knowledge base business logic
- `ai_service.py` - AI/RAG functionality
- `weather_service.py` - External weather API integration

### 3. Repository Layer (`app/repositories/`)
**Purpose**: Handle data access and database operations
- Execute database queries
- Map between database models and domain objects
- Provide CRUD operations
- **Only imports from**: Database models

**Files**:
- `destination_repository.py` - Destination data access
- `knowledge_repository.py` - Knowledge base data access

## Benefits of This Architecture

### 1. **Separation of Concerns**
- Each layer has a single responsibility
- Changes in one layer don't affect others
- Easy to understand and maintain

### 2. **Testability**
- Each layer can be unit tested independently
- Service layer can be tested without database
- Controllers can be tested with mocked services

### 3. **Flexibility**
- Database can be changed without affecting business logic
- Business rules are centralized in service layer
- API endpoints can be modified without changing data access

### 4. **Code Reusability**
- Services can be reused by different controllers
- Repositories can be shared across services
- Clear interfaces between layers

## Data Flow Example

```
1. POST /api/v1/destinations/
   ↓
2. destinations.py (Controller)
   - Validates request format
   - Calls DestinationService.create_destination()
   ↓
3. destination_service.py (Service)
   - Validates business rules (name uniqueness)
   - Calls DestinationRepository.create()
   ↓
4. destination_repository.py (Repository)
   - Creates database record
   - Returns Destination model
   ↓
5. Service returns to Controller
   ↓
6. Controller returns HTTP 201 with destination data
```

## Error Handling Strategy

### Repository Layer
- Returns None for not found
- Raises database-specific exceptions

### Service Layer
- Throws `ValueError` for business rule violations
- Handles repository exceptions
- Validates cross-entity relationships

### Controller Layer
- Catches service exceptions
- Maps to appropriate HTTP status codes
- Returns consistent error responses

## Import Rules

### Controllers (`app/api/`)
```python
# ✅ Allowed
from app.services.destination_service import DestinationService
from app.schemas.destination import DestinationCreate

# ❌ Not Allowed
from app.repositories.destination_repository import DestinationRepository
from app.models.destination import Destination
```

### Services (`app/services/`)
```python
# ✅ Allowed
from app.repositories.destination_repository import DestinationRepository
from app.schemas.destination import DestinationCreate
from app.models.destination import Destination

# ❌ Not Allowed
# Direct database imports (should go through repositories)
```

### Repositories (`app/repositories/`)
```python
# ✅ Allowed
from app.models.destination import Destination
from sqlalchemy.orm import Session

# ❌ Not Allowed
from app.schemas.destination import DestinationCreate
# (Repositories work with models, not schemas)
```

## File Structure

```
backend/app/
├── api/                    # Controllers (HTTP layer)
│   ├── __init__.py
│   ├── destinations.py     # Destination endpoints
│   ├── knowledge_base.py   # Knowledge base endpoints
│   └── ai_chat.py         # AI chat endpoints
│
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── destination_service.py
│   ├── knowledge_service.py
│   ├── ai_service.py
│   └── weather_service.py
│
├── repositories/          # Data access layer
│   ├── __init__.py
│   ├── destination_repository.py
│   └── knowledge_repository.py
│
├── models/               # Database models
│   ├── __init__.py
│   ├── destination.py
│   ├── knowledge_base.py
│   └── user.py
│
├── schemas/              # Pydantic schemas
│   ├── destination.py
│   ├── knowledge_base.py
│   └── ai_chat.py
│
└── core/                 # Core configurations
    ├── database.py
    └── settings.py
```

## Testing Strategy

### Unit Tests
- **Repository tests**: Test with in-memory database
- **Service tests**: Mock repository dependencies
- **Controller tests**: Mock service dependencies

### Integration Tests
- Test full request/response cycle
- Test with real database
- Validate error handling

This architecture provides a solid foundation for the AI Travel Advisor application with clear boundaries, testable components, and maintainable code structure.
