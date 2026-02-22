from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
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

class Character(Base, BaseModel):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    is_alive = Column(Boolean, default=True)

    player_owner = relationship("Player", back_populates="characters")
    match = relationship("Match", foreign_keys=[match_id], back_populates="participants")

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
    status = Column(String, default="pending")  # pending, active, completed
    
    # Blockchain-ready fields
    blockchain_tx_id = Column(String, nullable=True)
    blockchain_settlement_status = Column(String, nullable=True)  # pending, confirmed, failed

    participants = relationship("Character", foreign_keys="Character.match_id", back_populates="match")
    events = relationship("MatchEvent", back_populates="match")

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
