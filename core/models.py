# /home/ubuntu/coin_clash/core/models.py

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.sql import func
import logging
from .config_loader import load_config

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    wins = Column(Integer, default=0)
    kills = Column(Integer, default=0)
    total_sui_earned = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    characters = relationship("Character", back_populates="player_owner")
    inventory = relationship("PlayerItem", back_populates="player")

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_username = Column(String, ForeignKey("players.username"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True) # Nullable until assigned to a match
    is_alive = Column(Integer, default=1) # Use 1 for alive, 0 for dead for easier filtering
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    player_owner = relationship("Player", back_populates="characters")
    match = relationship("Match", foreign_keys=[match_id], back_populates="participants")

    @property
    def display_name(self):
        return f"{self.name} ({self.owner_username})"

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    entry_fee = Column(Float, nullable=False)
    kill_award_rate = Column(Float, nullable=False)
    start_method = Column(String) # "cap" or "timeout"
    start_threshold = Column(Integer) # cap number or timeout seconds
    start_timestamp = Column(DateTime(timezone=True))
    end_timestamp = Column(DateTime(timezone=True))
    winner_character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    status = Column(String, default="pending") # pending, active, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    participants = relationship("Character", foreign_keys="Character.match_id", back_populates="match")
    events = relationship("MatchEvent", back_populates="match")

class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False) # e.g., direct_kill, self, environmental, group, story, comeback, item_find
    scenario_source = Column(String) # e.g., scenario_id if loaded from file, or "generated" for others
    scenario_text = Column(Text, nullable=False)
    affected_character_ids = Column(String) # Comma-separated list of character IDs
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="events")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String) # e.g., cosmetic, gear, consumable
    rarity = Column(String) # e.g., common, rare, legendary
    description = Column(Text)
    # Hooks could be implemented as methods in a service layer or stored as strings/JSON
    # For simplicity, we'll just store info here.
    on_find_hook_info = Column(String, nullable=True)
    on_award_hook_info = Column(String, nullable=True)

    player_items = relationship("PlayerItem", back_populates="item")

class PlayerItem(Base):
    __tablename__ = "player_items"
    # Association object for many-to-many between Player and Item
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())

    player = relationship("Player", back_populates="inventory")
    item = relationship("Item", back_populates="player_items")

# Database setup
config = load_config()
DATABASE_URL = config["database_url"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# Example usage (can be moved to main script later)
# if __name__ == "__main__":
#     init_db()
#     print("Database initialized!")

