import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.db.session import get_db_dependency
from app.main import app
from app.models.models import Player
from app.services.auth.dependencies import get_current_player

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

_current_player_override: Player | None = None


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_player():
    if _current_player_override is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return _current_player_override


app.dependency_overrides[get_db_dependency] = override_get_db
app.dependency_overrides[get_current_player] = override_get_current_player


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate all tables before each test for isolation."""
    global _current_player_override
    _current_player_override = None
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_player(test_db):
    """Create a player in the test DB and set it as the authenticated player."""
    global _current_player_override
    p = Player(wallet_address="0xTestWallet", username="testplayer", balance=100.0, wins=5, kills=10, total_earnings=50.0)
    test_db.add(p)
    test_db.commit()
    test_db.refresh(p)
    _current_player_override = p
    return p
