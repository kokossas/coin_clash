from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean,
    Numeric, CheckConstraint, Index, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base_class import Base, BaseModel

class Player(Base, BaseModel):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    wallet_address = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)  # display name, auto-assigned if null
    balance = Column(Float, default=0.0)
    wins = Column(Integer, default=0)
    kills = Column(Integer, default=0)
    total_sui_earned = Column(Float, default=0.0)
    wallet_chain_id = Column(String, nullable=True)

    characters = relationship("Character", back_populates="player_owner")
    inventory = relationship("PlayerItem", back_populates="player")
    transactions = relationship("Transaction", back_populates="player")
    owned_characters = relationship("OwnedCharacter", back_populates="player")

class Character(Base, BaseModel):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    is_alive = Column(Boolean, default=True)
    owned_character_id = Column(Integer, ForeignKey("owned_characters.id"), nullable=True)
    entry_order = Column(Integer, nullable=False, default=0)
    elimination_round = Column(Integer, nullable=True)

    player_owner = relationship("Player", back_populates="characters")
    match = relationship("Match", foreign_keys=[match_id], back_populates="participants")
    owned_character = relationship("OwnedCharacter", back_populates="match_characters")

    @property
    def display_name(self):
        return f"{self.name} ({self.player_owner.username})"

class Match(Base, BaseModel):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    entry_fee = Column(Float, nullable=False)
    kill_award_rate = Column(Float, nullable=False)
    start_method = Column(String)  # "cap" or "timeout"
    start_threshold = Column(Integer)  # cap number or timeout seconds
    start_timer_end = Column(DateTime(timezone=True), nullable=True)
    start_timestamp = Column(DateTime(timezone=True))
    end_timestamp = Column(DateTime(timezone=True))
    winner_character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    status = Column(String, default="pending")  # pending, filling, active, completed, cancelled, failed
    
    # Blockchain-ready fields
    blockchain_tx_id = Column(String, nullable=True)
    blockchain_settlement_status = Column(String, nullable=True)  # pending, confirmed, failed

    # Lobby fields
    creator_wallet_address = Column(String(100), nullable=True)
    min_players = Column(Integer, default=3)
    max_characters = Column(Integer, default=20)
    max_characters_per_player = Column(Integer, default=3)
    protocol_fee_percentage = Column(Numeric(5, 2), default=10.0)
    countdown_started_at = Column(DateTime(timezone=True), nullable=True)

    participants = relationship("Character", foreign_keys="Character.match_id", back_populates="match")
    events = relationship("MatchEvent", back_populates="match")
    join_requests = relationship("MatchJoinRequest", back_populates="match")
    pending_payouts = relationship("PendingPayout", back_populates="match")

class MatchEvent(Base, BaseModel):
    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    scenario_source = Column(String)
    scenario_text = Column(Text, nullable=False)
    affected_character_ids = Column(String)

    match = relationship("Match", back_populates="events")

class Item(Base, BaseModel):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String)
    rarity = Column(String)
    description = Column(Text)
    on_find_hook_info = Column(String, nullable=True)
    on_award_hook_info = Column(String, nullable=True)
    
    # Blockchain-ready fields
    token_id = Column(String, nullable=True)
    token_uri = Column(String, nullable=True)

    player_items = relationship("PlayerItem", back_populates="item")

class PlayerItem(Base, BaseModel):
    __tablename__ = "player_items"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    quantity = Column(Integer, default=1)

    player = relationship("Player", back_populates="inventory")
    item = relationship("Item", back_populates="player_items")

class Transaction(Base, BaseModel):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    tx_type = Column(String, nullable=False)  # deposit, withdrawal, match_entry, prize_payout
    status = Column(String, nullable=False)  # pending, completed, failed
    provider = Column(String, nullable=False)  # traditional, polygon, solana, etc.
    provider_tx_id = Column(String, nullable=True)  # For blockchain transaction hash
    
    player = relationship("Player", back_populates="transactions")


class OwnedCharacter(Base, BaseModel):
    __tablename__ = "owned_characters"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    character_name = Column(String(50), nullable=False)
    is_alive = Column(Boolean, default=True)
    last_match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    revival_count = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_owned_characters_player_alive", "player_id", "is_alive"),
        Index("ix_owned_characters_last_match", "last_match_id"),
    )

    player = relationship("Player", back_populates="owned_characters")
    last_match = relationship("Match", foreign_keys=[last_match_id])
    match_characters = relationship("Character", back_populates="owned_character")


class MatchJoinRequest(Base, BaseModel):
    __tablename__ = "match_join_requests"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    entry_fee_total = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(String(20), default="pending")
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "payment_status IN ('pending', 'confirmed', 'failed')",
            name="ck_match_join_requests_payment_status",
        ),
        Index("ix_match_join_requests_match_player", "match_id", "player_id"),
        Index("ix_match_join_requests_payment_status", "payment_status"),
    )

    match = relationship("Match", back_populates="join_requests")
    player = relationship("Player")
    characters = relationship("MatchJoinRequestCharacter", back_populates="join_request")


class MatchJoinRequestCharacter(Base):
    """Junction table — no timestamps needed."""
    __tablename__ = "match_join_request_characters"

    join_request_id = Column(Integer, ForeignKey("match_join_requests.id"), primary_key=True)
    owned_character_id = Column(Integer, ForeignKey("owned_characters.id"), primary_key=True)

    join_request = relationship("MatchJoinRequest", back_populates="characters")
    owned_character = relationship("OwnedCharacter")


class PendingPayout(Base, BaseModel):
    __tablename__ = "pending_payouts"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    payout_type = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USDC")
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    settlement_tx_hash = Column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "payout_type IN ('kill_award', 'winner', 'refund')",
            name="ck_pending_payouts_payout_type",
        ),
        CheckConstraint("amount > 0", name="ck_pending_payouts_amount_positive"),
        Index("ix_pending_payouts_match", "match_id"),
        Index("ix_pending_payouts_player", "player_id"),
        Index(
            "ix_pending_payouts_unsettled",
            "settled_at",
            postgresql_where=text("settled_at IS NULL"),
        ),
    )

    match = relationship("Match", back_populates="pending_payouts")
    player = relationship("Player")
