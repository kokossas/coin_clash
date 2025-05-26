# Coin Clash: Incremental Migration Tasks

This document breaks down the Phase 1 development tasks from the incremental migration plan, focusing on database migration and API layer implementation while preparing for future blockchain integration.

## Table of Contents
- [1. Project Setup](#1-project-setup)
- [2. Database Migration](#2-database-migration)
- [3. Core API Framework](#3-core-api-framework)
- [4. Authentication System](#4-authentication-system)
- [5. Player Management API](#5-player-management-api)
- [6. Match Management API](#6-match-management-api)
- [7. Character Management API](#7-character-management-api)
- [8. Frontend Integration](#8-frontend-integration)
- [9. Testing and Documentation](#9-testing-and-documentation)
- [10. Deployment](#10-deployment)

## 1. Project Setup

### 1.1 Development Environment Configuration
- [ ] **Task**: Set up development environment with Docker for local testing
- **Files/Modules**:
  - `/docker-compose.yml` - Docker Compose configuration
  - `/backend/Dockerfile` - Backend Docker configuration
  - `/frontend/Dockerfile` - Frontend Docker configuration
  - `/.env.example` - Example environment variables
- **Details**:
  - Configure PostgreSQL service in Docker Compose
  - Set up FastAPI backend service
  - Configure Next.js frontend service
  - Include environment variables for database connection
- **Owner**: DevOps
- **Estimate**: 1 day

### 1.2 Project Structure Setup
- [ ] **Task**: Create base project structure for the full-stack application
- **Files/Modules**:
  - `/backend/` - Python backend directory
  - `/frontend/` - Next.js frontend directory
  - `/backend/app/` - FastAPI application directory
  - `/backend/app/api/` - API routes directory
  - `/backend/app/core/` - Core business logic (migrated from existing codebase)
  - `/backend/app/db/` - Database models and connection
  - `/backend/app/schemas/` - Pydantic schemas for API
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 1.3 Dependency Management
- [ ] **Task**: Set up dependency management for backend and frontend
- **Files/Modules**:
  - `/backend/requirements.txt` - Python dependencies
  - `/frontend/package.json` - Node.js dependencies
- **Dependencies**:
  - Backend: FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, psycopg2-binary, python-jose, passlib
  - Frontend: Next.js, React, Chakra UI, Redux Toolkit, Axios
- **Owner**: Backend Lead & Frontend Lead
- **Estimate**: 1 day

## 2. Database Migration

### 2.1 PostgreSQL Connection Setup
- [ ] **Task**: Configure PostgreSQL connection and environment
- **Files/Modules**:
  - `/backend/app/db/session.py` - Database session management
  - `/backend/app/core/config.py` - Configuration management
- **Code Example**:
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker
  
  from app.core.config import settings
  
  engine = create_engine(settings.DATABASE_URL)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  Base = declarative_base()
  
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 2.2 Base Models Migration
- [ ] **Task**: Migrate existing SQLite models to PostgreSQL-compatible models
- **Files/Modules**:
  - `/backend/app/db/base_class.py` - Base model class
  - `/backend/app/models/player.py` - Player model
  - `/backend/app/models/character.py` - Character model
  - `/backend/app/models/match.py` - Match model
  - `/backend/app/models/event.py` - Event model
  - `/backend/app/models/item.py` - Item model
- **Changes**:
  - Update SQLAlchemy model definitions for PostgreSQL compatibility
  - Add created_at and updated_at timestamps to all models
  - Add indexes for frequently queried fields
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 2.3 Blockchain-Ready Model Extensions
- [ ] **Task**: Extend models with fields for future blockchain integration
- **Files/Modules**:
  - `/backend/app/models/player.py` - Add wallet-related fields
  - `/backend/app/models/match.py` - Add blockchain settlement fields
  - `/backend/app/models/transaction.py` - New transaction model
- **Model Extensions**:
  ```python
  # Player model extension
  class Player(Base):
      # Existing fields...
      wallet_address = Column(String, nullable=True)  # For future blockchain integration
      wallet_chain_id = Column(String, nullable=True)  # For future multi-chain support
      
  # New Transaction model
  class Transaction(Base):
      __tablename__ = "transactions"
      
      id = Column(Integer, primary_key=True)
      player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
      amount = Column(Float, nullable=False)
      currency = Column(String, nullable=False)
      tx_type = Column(String, nullable=False)  # deposit, withdrawal, match_entry, prize_payout
      status = Column(String, nullable=False)  # pending, completed, failed
      provider = Column(String, nullable=False)  # traditional, polygon, solana, etc.
      provider_tx_id = Column(String, nullable=True)  # For blockchain transaction hash
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      updated_at = Column(DateTime(timezone=True), onupdate=func.now())
      
      player = relationship("Player", back_populates="transactions")
  
  # Update Player model to include relationship
  class Player(Base):
      # Existing fields...
      transactions = relationship("Transaction", back_populates="player")
  ```
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 2.4 Alembic Migration Setup
- [ ] **Task**: Set up Alembic for database migrations
- **Files/Modules**:
  - `/backend/alembic.ini` - Alembic configuration
  - `/backend/alembic/env.py` - Alembic environment
  - `/backend/alembic/versions/` - Migration scripts
- **Commands**:
  ```bash
  # Initialize Alembic
  alembic init alembic
  
  # Create initial migration
  alembic revision --autogenerate -m "Initial migration"
  
  # Run migrations
  alembic upgrade head
  ```
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 2.5 Data Migration Script
- [ ] **Task**: Create script to migrate data from SQLite to PostgreSQL
- **Files/Modules**:
  - `/backend/scripts/migrate_data.py` - Data migration script
- **Functionality**:
  - Connect to SQLite database
  - Extract data from all tables
  - Connect to PostgreSQL database
  - Insert data into corresponding tables
  - Handle data type conversions
  - Validate migration success
- **Owner**: Backend Lead
- **Estimate**: 2 days

## 3. Core API Framework

### 3.1 FastAPI Application Setup
- [ ] **Task**: Set up FastAPI application with middleware and configuration
- **Files/Modules**:
  - `/backend/app/main.py` - Main FastAPI application
  - `/backend/app/api/deps.py` - Dependency injection
  - `/backend/app/middleware/` - Middleware components
- **Code Example**:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  
  from app.api.api_v1.api import api_router
  from app.core.config import settings
  
  app = FastAPI(
      title=settings.PROJECT_NAME,
      openapi_url=f"{settings.API_V1_STR}/openapi.json"
  )
  
  # Set up CORS
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.BACKEND_CORS_ORIGINS,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  app.include_router(api_router, prefix=settings.API_V1_STR)
  ```
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 3.2 API Router Structure
- [ ] **Task**: Set up API router structure with versioning
- **Files/Modules**:
  - `/backend/app/api/api_v1/api.py` - Main API router
  - `/backend/app/api/api_v1/endpoints/` - Endpoint modules
- **Code Example**:
  ```python
  from fastapi import APIRouter
  
  from app.api.api_v1.endpoints import players, matches, characters, auth
  
  api_router = APIRouter()
  api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
  api_router.include_router(players.router, prefix="/players", tags=["players"])
  api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
  api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
  ```
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 3.3 Pydantic Schema Setup
- [ ] **Task**: Create Pydantic schemas for request/response models
- **Files/Modules**:
  - `/backend/app/schemas/player.py` - Player schemas
  - `/backend/app/schemas/character.py` - Character schemas
  - `/backend/app/schemas/match.py` - Match schemas
  - `/backend/app/schemas/token.py` - Authentication token schemas
- **Code Example**:
  ```python
  from pydantic import BaseModel
  from typing import List, Optional
  from datetime import datetime
  
  class PlayerBase(BaseModel):
      username: str
  
  class PlayerCreate(PlayerBase):
      pass
  
  class PlayerUpdate(PlayerBase):
      username: Optional[str] = None
  
  class PlayerInDBBase(PlayerBase):
      id: int
      balance: float
      wins: int
      kills: int
      total_sui_earned: float
      created_at: datetime
      
      class Config:
          orm_mode = True
  
  class Player(PlayerInDBBase):
      pass
  ```
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 3.4 Repository Pattern Implementation
- [ ] **Task**: Implement repository pattern for database access
- **Files/Modules**:
  - `/backend/app/crud/base.py` - Base CRUD repository
  - `/backend/app/crud/player.py` - Player repository
  - `/backend/app/crud/character.py` - Character repository
  - `/backend/app/crud/match.py` - Match repository
- **Code Example**:
  ```python
  from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
  
  from fastapi.encoders import jsonable_encoder
  from pydantic import BaseModel
  from sqlalchemy.orm import Session
  
  from app.db.base_class import Base
  
  ModelType = TypeVar("ModelType", bound=Base)
  CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
  UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
  
  class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
      def __init__(self, model: Type[ModelType]):
          self.model = model
  
      def get(self, db: Session, id: Any) -> Optional[ModelType]:
          return db.query(self.model).filter(self.model.id == id).first()
  
      def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
          return db.query(self.model).offset(skip).limit(limit).all()
  
      def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
          obj_in_data = jsonable_encoder(obj_in)
          db_obj = self.model(**obj_in_data)
          db.add(db_obj)
          db.commit()
          db.refresh(db_obj)
          return db_obj
  
      def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
          obj_data = jsonable_encoder(db_obj)
          if isinstance(obj_in, dict):
              update_data = obj_in
          else:
              update_data = obj_in.dict(exclude_unset=True)
          for field in obj_data:
              if field in update_data:
                  setattr(db_obj, field, update_data[field])
          db.add(db_obj)
          db.commit()
          db.refresh(db_obj)
          return db_obj
  
      def remove(self, db: Session, *, id: int) -> ModelType:
          obj = db.query(self.model).get(id)
          db.delete(obj)
          db.commit()
          return obj
  ```
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 3.5 Service Layer Implementation
- [ ] **Task**: Implement service layer for business logic
- **Files/Modules**:
  - `/backend/app/services/base.py` - Base service class
  - `/backend/app/services/player_service.py` - Player service
  - `/backend/app/services/match_service.py` - Match service
  - `/backend/app/services/character_service.py` - Character service
- **Owner**: Backend Lead
- **Estimate**: 3 days

### 3.6 Payment Provider Interface
- [ ] **Task**: Create abstract payment provider interface for future blockchain integration
- **Files/Modules**:
  - `/backend/app/services/payment/base.py` - Base payment provider interface
  - `/backend/app/services/payment/mock_provider.py` - Mock payment provider for testing
- **Owner**: Backend Lead
- **Estimate**: 2 days

## 4. Authentication System

### 4.1 Authentication Service
- [ ] **Task**: Implement authentication service with provider interface
- **Files/Modules**:
  - `/backend/app/services/auth/base.py` - Base authentication provider interface
  - `/backend/app/services/auth/jwt_provider.py` - JWT authentication provider
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 4.2 User Management
- [ ] **Task**: Implement user management endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/users.py` - User endpoints
  - `/backend/app/schemas/user.py` - User schemas
  - `/backend/app/models/user.py` - User model
  - `/backend/app/crud/user.py` - User repository
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 4.3 JWT Token Handling
- [ ] **Task**: Implement JWT token generation and validation
- **Files/Modules**:
  - `/backend/app/core/security.py` - Security utilities
  - `/backend/app/api/deps.py` - Authentication dependencies
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 4.4 Password Hashing
- [ ] **Task**: Implement password hashing and verification
- **Files/Modules**:
  - `/backend/app/core/security.py` - Security utilities
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 4.5 Authentication Endpoints
- [ ] **Task**: Implement authentication endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/auth.py` - Authentication endpoints
  - `/backend/app/schemas/token.py` - Token schemas
- **Owner**: Backend Lead
- **Estimate**: 1 day

## 5. Player Management API

### 5.1 Player Model and Schema
- [ ] **Task**: Implement player model and schema
- **Files/Modules**:
  - `/backend/app/models/player.py` - Player model
  - `/backend/app/schemas/player.py` - Player schemas
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 5.2 Player Repository
- [ ] **Task**: Implement player repository
- **Files/Modules**:
  - `/backend/app/crud/player.py` - Player repository
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 5.3 Player Service
- [ ] **Task**: Implement player service
- **Files/Modules**:
  - `/backend/app/services/player_service.py` - Player service
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 5.4 Player Endpoints
- [ ] **Task**: Implement player endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/players.py` - Player endpoints
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 5.5 Player Statistics
- [ ] **Task**: Implement player statistics endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/players.py` - Player endpoints
  - `/backend/app/services/player_service.py` - Player service
- **Owner**: Backend Lead
- **Estimate**: 1 day

## 6. Match Management API

### 6.1 Match Model and Schema
- [ ] **Task**: Implement match model and schema
- **Files/Modules**:
  - `/backend/app/models/match.py` - Match model
  - `/backend/app/schemas/match.py` - Match schemas
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 6.2 Match Repository
- [ ] **Task**: Implement match repository
- **Files/Modules**:
  - `/backend/app/crud/match.py` - Match repository
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 6.3 Match Service
- [ ] **Task**: Implement match service
- **Files/Modules**:
  - `/backend/app/services/match_service.py` - Match service
- **Owner**: Backend Lead
- **Estimate**: 2 days

### 6.4 Match Endpoints
- [ ] **Task**: Implement match endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/matches.py` - Match endpoints
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 6.5 Match Execution
- [ ] **Task**: Implement match execution
- **Files/Modules**:
  - `/backend/app/services/match_service.py` - Match service
  - `/backend/app/core/match_engine.py` - Match engine
- **Owner**: Backend Lead
- **Estimate**: 3 days

### 6.6 Match Results
- [ ] **Task**: Implement match results
- **Files/Modules**:
  - `/backend/app/services/match_service.py` - Match service
  - `/backend/app/api/api_v1/endpoints/matches.py` - Match endpoints
- **Owner**: Backend Lead
- **Estimate**: 2 days

## 7. Character Management API

### 7.1 Character Model and Schema
- [ ] **Task**: Implement character model and schema
- **Files/Modules**:
  - `/backend/app/models/character.py` - Character model
  - `/backend/app/schemas/character.py` - Character schemas
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 7.2 Character Repository
- [ ] **Task**: Implement character repository
- **Files/Modules**:
  - `/backend/app/crud/character.py` - Character repository
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 7.3 Character Service
- [ ] **Task**: Implement character service
- **Files/Modules**:
  - `/backend/app/services/character_service.py` - Character service
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 7.4 Character Endpoints
- [ ] **Task**: Implement character endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/characters.py` - Character endpoints
- **Owner**: Backend Lead
- **Estimate**: 1 day

## 8. Frontend Integration

### 8.1 Next.js Setup
- [ ] **Task**: Set up Next.js frontend
- **Files/Modules**:
  - `/frontend/` - Next.js frontend directory
- **Owner**: Frontend Lead
- **Estimate**: 1 day

### 8.2 API Client
- [ ] **Task**: Implement API client
- **Files/Modules**:
  - `/frontend/src/api/` - API client
- **Owner**: Frontend Lead
- **Estimate**: 2 days

### 8.3 Authentication UI
- [ ] **Task**: Implement authentication UI
- **Files/Modules**:
  - `/frontend/src/components/auth/` - Authentication components
  - `/frontend/src/pages/auth/` - Authentication pages
- **Owner**: Frontend Lead
- **Estimate**: 2 days

### 8.4 Player UI
- [ ] **Task**: Implement player UI
- **Files/Modules**:
  - `/frontend/src/components/player/` - Player components
  - `/frontend/src/pages/player/` - Player pages
- **Owner**: Frontend Lead
- **Estimate**: 2 days

### 8.5 Match UI
- [ ] **Task**: Implement match UI
- **Files/Modules**:
  - `/frontend/src/components/match/` - Match components
  - `/frontend/src/pages/match/` - Match pages
- **Owner**: Frontend Lead
- **Estimate**: 3 days

### 8.6 Character UI
- [ ] **Task**: Implement character UI
- **Files/Modules**:
  - `/frontend/src/components/character/` - Character components
  - `/frontend/src/pages/character/` - Character pages
- **Owner**: Frontend Lead
- **Estimate**: 2 days

## 9. Testing and Documentation

### 9.1 Unit Tests
- [ ] **Task**: Implement unit tests
- **Files/Modules**:
  - `/backend/tests/` - Backend tests
  - `/frontend/tests/` - Frontend tests
- **Owner**: QA Lead
- **Estimate**: 5 days

### 9.2 Integration Tests
- [ ] **Task**: Implement integration tests
- **Files/Modules**:
  - `/backend/tests/` - Backend tests
- **Owner**: QA Lead
- **Estimate**: 3 days

### 9.3 API Documentation
- [ ] **Task**: Generate API documentation
- **Files/Modules**:
  - `/backend/app/main.py` - FastAPI application
- **Owner**: Backend Lead
- **Estimate**: 1 day

### 9.4 User Documentation
- [ ] **Task**: Create user documentation
- **Files/Modules**:
  - `/docs/` - Documentation directory
- **Owner**: Documentation Lead
- **Estimate**: 3 days

## 10. Deployment

### 10.1 Docker Compose Setup
- [ ] **Task**: Set up Docker Compose for production
- **Files/Modules**:
  - `/docker-compose.prod.yml` - Production Docker Compose configuration
- **Owner**: DevOps
- **Estimate**: 1 day

### 10.2 CI/CD Pipeline
- [ ] **Task**: Set up CI/CD pipeline
- **Files/Modules**:
  - `/.github/workflows/` - GitHub Actions workflows
- **Owner**: DevOps
- **Estimate**: 2 days

### 10.3 Production Deployment
- [ ] **Task**: Deploy to production
- **Files/Modules**:
  - `/scripts/deploy.sh` - Deployment script
- **Owner**: DevOps
- **Estimate**: 1 day

## Discovered During Work
- [ ] **Task**: Add any new tasks discovered during development here
