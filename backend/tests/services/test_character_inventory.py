"""Tests for CharacterInventoryService — validation guards and state transitions."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.models.models import Player, Character, Match, OwnedCharacter
from app.services.character_inventory import CharacterInventoryService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_payment():
    provider = AsyncMock()
    provider.process_deposit.return_value = {
        "success": True,
        "transaction_id": "mock-tx-1",
        "status": "completed",
        "amount": 1.0,
        "currency": "USDC",
    }
    return provider


@pytest.fixture
def service(mock_payment):
    with patch(
        "app.services.character_inventory.BlockchainServiceFactory.get_payment_provider",
        return_value=mock_payment,
    ), patch(
        "app.services.character_inventory.load_config",
        return_value=MagicMock(character_base_price=1.0, character_revival_fee=0.5),
    ):
        svc = CharacterInventoryService()
    return svc


@pytest.fixture
def player(db_session):
    p = Player(wallet_address="0xabc123", username="tester", balance=100.0)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def dead_owned_char(db_session, player):
    oc = OwnedCharacter(
        player_id=player.id,
        character_name="DeadGuy",
        is_alive=False,
        revival_count=0,
    )
    db_session.add(oc)
    db_session.commit()
    db_session.refresh(oc)
    return oc


@pytest.fixture
def alive_owned_char(db_session, player):
    oc = OwnedCharacter(
        player_id=player.id,
        character_name="AliveGuy",
        is_alive=True,
        revival_count=0,
    )
    db_session.add(oc)
    db_session.commit()
    db_session.refresh(oc)
    return oc


class TestPurchaseCharacters:

    @pytest.mark.asyncio
    async def test_creates_correct_quantity(self, service, db_session, player):
        result = await service.purchase_characters(db_session, player.id, 3, "0xabc123")
        assert len(result) == 3
        assert all(oc.player_id == player.id for oc in result)
        assert all(oc.is_alive is True for oc in result)

    @pytest.mark.asyncio
    async def test_quantity_below_min_raises(self, service, db_session, player):
        with pytest.raises(ValueError, match="quantity"):
            await service.purchase_characters(db_session, player.id, 0, "0xabc123")

    @pytest.mark.asyncio
    async def test_quantity_above_max_raises(self, service, db_session, player):
        with pytest.raises(ValueError, match="quantity"):
            await service.purchase_characters(db_session, player.id, 11, "0xabc123")

    @pytest.mark.asyncio
    async def test_nonexistent_player_raises(self, service, db_session):
        with pytest.raises(ValueError, match="not found"):
            await service.purchase_characters(db_session, 9999, 1, "0xwallet")


class TestReviveCharacter:

    @pytest.mark.asyncio
    async def test_revive_dead_character(self, service, db_session, player, dead_owned_char):
        result = await service.revive_character(
            db_session, dead_owned_char.id, player.id, "0xabc123"
        )
        assert result.is_alive is True
        assert result.revival_count == 1

    @pytest.mark.asyncio
    async def test_revive_already_alive_raises(self, service, db_session, player, alive_owned_char):
        with pytest.raises(ValueError, match="already alive"):
            await service.revive_character(
                db_session, alive_owned_char.id, player.id, "0xabc123"
            )

    @pytest.mark.asyncio
    async def test_revive_wrong_player_raises(self, service, db_session, dead_owned_char):
        other = Player(wallet_address="0xother", username="other")
        db_session.add(other)
        db_session.commit()
        db_session.refresh(other)

        with pytest.raises(ValueError, match="not owned"):
            await service.revive_character(
                db_session, dead_owned_char.id, other.id, "0xother"
            )

    @pytest.mark.asyncio
    async def test_revive_nonexistent_raises(self, service, db_session, player):
        with pytest.raises(ValueError, match="not found"):
            await service.revive_character(db_session, 9999, player.id, "0xabc123")


    @pytest.mark.asyncio
    async def test_revive_in_active_match_raises(self, service, db_session, player, dead_owned_char):
        # Create an active match with a Character linked to this owned character
        match = Match(
            entry_fee=1.0,
            kill_award_rate=0.1,
            start_method="cap",
            start_threshold=10,
            status="active",
        )
        db_session.add(match)
        db_session.flush()

        char = Character(
            name="InMatch",
            player_id=player.id,
            match_id=match.id,
            owned_character_id=dead_owned_char.id,
        )
        db_session.add(char)
        db_session.commit()

        with pytest.raises(ValueError, match="active match"):
            await service.revive_character(
                db_session, dead_owned_char.id, player.id, "0xabc123"
            )
