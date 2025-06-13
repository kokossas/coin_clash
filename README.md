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

The project is currently in Phase 2 of an incremental migration plan:

- ✅ Phase 1: Database migration from SQLite to PostgreSQL
  - ✅ REST API implementation with FastAPI
  - ✅ Authentication system with JWT
  - ✅ Service layer abstraction
  - ✅ Blockchain integration preparation

- ✅ Phase 2: Blockchain Abstraction Layer (Current)
  - ✅ Wallet interface and mock provider
  - ✅ Payment interface and mock provider
  - ✅ Transaction interface and mock provider
  - ✅ Asset interface and mock provider
  - ✅ Blockchain error handling and retry mechanisms
  - ✅ Service factory for provider management

- 🔄 Phase 3: Blockchain Integration (Next)
  - 🔄 Polygon and Solana provider implementations
  - 🔄 Smart contract integration
  - 🔄 Frontend wallet connection

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
    /services/      
      /auth/        # Authentication services
      /blockchain/  # Blockchain abstraction layer
        /wallet/    # Wallet connection and verification
        /payment/   # Deposits and withdrawals
        /transaction/ # Blockchain transactions
        /asset/     # Asset management (NFTs)
      /payment/     # Payment processing
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
- pytest-asyncio (for running blockchain abstraction tests)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/kokossas/coin_clash.git
   cd coin_clash
   git checkout phase2_blockchain_abs
   ```

2. Install dependencies:
   ```
   pip install -r backend/requirements.txt
   pip install pytest-asyncio  # Required for blockchain tests
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
# Run all tests
pytest backend/tests/

# Run blockchain abstraction tests specifically
pytest backend/tests/services/blockchain/
```

## Blockchain Abstraction Layer

The blockchain abstraction layer provides a clean separation between game logic and blockchain implementations, allowing for:

- Development and testing without actual blockchain dependencies
- Support for multiple blockchain networks (Polygon, Solana)
- Consistent error handling and retry mechanisms
- Future extensibility for additional chains

### Key Components

- **Wallet Interface**: Connect to wallets, verify signatures, manage chain support
- **Payment Interface**: Process deposits/withdrawals, check balances, estimate fees
- **Transaction Interface**: Create and monitor blockchain transactions
- **Asset Interface**: Create, transfer, and update blockchain assets (NFTs)

### Mock Providers

All interfaces include mock implementations that simulate blockchain behavior with:
- Configurable network delays
- Simulated transaction lifecycles
- Realistic error scenarios
- In-memory state management

For detailed documentation, see [PHASE2_CHANGES.md](PHASE2_CHANGES.md).

## API Documentation

Once the server is running, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Roadmap

The project is following an incremental migration approach:

1. **Phase 1: Database and API Layer** (Completed)
   - PostgreSQL migration
   - REST API implementation
   - Authentication system
   - Service layer abstraction

2. **Phase 2: Blockchain Abstraction Layer** (Current)
   - Wallet interface and mock provider
   - Payment interface and mock provider
   - Transaction interface and mock provider
   - Asset interface and mock provider
   - Blockchain error handling and retry mechanisms

3. **Phase 3: Blockchain Integration** (Next)
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
2. Create a feature branch from the current phase branch
3. Implement your changes with tests
4. Submit a pull request

## License

[License information]
