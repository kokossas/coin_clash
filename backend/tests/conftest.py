import pytest
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.base_class import Base
from app.models.models import Player, Character, Match, MatchEvent, Item, PlayerItem, Transaction
from app.core.config import settings

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


def _random_string(k: int = 10) -> str:
    return ''.join(random.choices(string.ascii_lowercase, k=k))


# Expose on pytest namespace for API tests that use it inline
pytest.random_string = _random_string


@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_player(db_session):
    player = Player(
        wallet_address=f"0x{_random_string(40)}",
        username="test_user",
        balance=100.0,
        wins=5,
        kills=10,
        total_earnings=50.0
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


@pytest.fixture
def test_character(db_session, test_player):
    character = Character(
        name="Test Character",
        player_id=test_player.id,
        is_alive=True
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)
    return character


@pytest.fixture
def test_match(db_session):
    match = Match(
        entry_fee=1.0,
        kill_award_rate=0.5,
        start_method="cap",
        start_threshold=10,
        status="pending"
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


@pytest.fixture
def test_transaction(db_session, test_player):
    transaction = Transaction(
        player_id=test_player.id,
        amount=10.0,
        currency="USDC",
        tx_type="deposit",
        status="completed",
        provider="mock"
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction
