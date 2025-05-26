# Coin Clash

Coin Clash is a backend game engine being transformed into a full-stack Web3 game through an incremental migration approach.

## Project Overview

Coin Clash is a multiplayer game where players purchase characters to enter matches, compete for survival, and earn rewards. The game features:

- Character purchase and management
- Match creation and participation
- Real-time match simulation with various event types
- Player statistics and rewards

This repository contains the backend game engine and the ongoing migration to a modern API-based architecture with future blockchain integration capabilities.

## Migration Status

The project is currently in Phase 1 of an incremental migration plan:

- ✅ Database migration from SQLite to PostgreSQL
- ✅ REST API implementation with FastAPI
- ✅ Authentication system with JWT
- ✅ Service layer abstraction
- ✅ Blockchain integration preparation
- 🔄 Frontend development (in progress)

## Project Structure

```
/backend/
  /app/
    /api/           # API endpoints
    /core/          # Core business logic
    /crud/          # Database operations
    /db/            # Database connection and models
    /models/        # SQLAlchemy models
    /schemas/       # Pydantic schemas
    /services/      # Business logic services
    main.py         # FastAPI application
  /tests/           # Test suite
/core/              # Original game engine
/scenarios/         # Game scenarios
/tests/             # Original tests
```

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/kokossas/coin_clash.git
   cd coin_clash
   git checkout migration
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL:
   ```
   # Create a PostgreSQL database
   createdb coin_clash
   
   # Or use Docker
   docker-compose up -d postgres
   ```

4. Run database migrations:
   ```
   # Once Alembic is set up
   alembic upgrade head
   ```

5. Start the API server:
   ```
   uvicorn backend.app.main:app --reload
   ```

### Running Tests

```
pytest backend/tests/
```

## API Documentation

Once the server is running, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Roadmap

The project is following an incremental migration approach:

1. **Phase 1: Database and API Layer** (Current)
   - PostgreSQL migration
   - REST API implementation
   - Authentication system
   - Service layer abstraction

2. **Phase 2: Blockchain Abstraction Layer** (Next)
   - Refine payment provider interfaces
   - Develop blockchain transaction models
   - Create wallet interaction abstractions
   - Implement mock blockchain services

3. **Phase 3: Blockchain Integration**
   - Wallet integration
   - Smart contract development
   - Blockchain transaction monitoring
   - Token management

4. **Phase 4: Advanced Features**
   - Tournament system
   - Social features
   - Marketplace integration
   - Advanced analytics

## Contributing

1. Check the `TASK.md` file for current development tasks
2. Create a feature branch from `migration`
3. Implement your changes with tests
4. Submit a pull request

## License

[License information]

