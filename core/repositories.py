# /home/ubuntu/coin_clash/core/repositories.py

import datetime # Added missing import
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import Player, Character, Match, MatchEvent, Item, PlayerItem, init_db
from .db import get_session

# Initialize DB if it doesn't exist
init_db()

# --- Repository Interfaces (Abstract Base Classes) ---

class BaseRepo(ABC):
    def __init__(self, db_session: Session):
        self.db = db_session

class PlayerRepo(BaseRepo):
    @abstractmethod
    def get_player_by_username(self, username: str) -> Optional[Player]:
        pass

    @abstractmethod
    def create_player(self, username: str) -> Player:
        pass

    @abstractmethod
    def update_player_balance(self, player_id: int, amount_change: float) -> Optional[Player]:
        pass

    @abstractmethod
    def add_win(self, player_id: int) -> Optional[Player]:
        pass

    @abstractmethod
    def add_kill(self, player_id: int) -> Optional[Player]:
        pass

    @abstractmethod
    def add_sui_earned(self, player_id: int, amount: float) -> Optional[Player]:
        pass

    @abstractmethod
    def get_player_inventory(self, player_id: int) -> List[PlayerItem]:
        pass

    @abstractmethod
    def add_item_to_inventory(self, player_id: int, item_id: int, quantity: int = 1) -> Optional[PlayerItem]:
        pass

    @abstractmethod
    def get_or_create_player(self, username: str) -> Player:
        pass

    @abstractmethod
    def get_all_players(self, limit: int = 100) -> List[Player]:
        pass

class CharacterRepo(BaseRepo):
    @abstractmethod
    def create_character(self, name: str, owner_username: str) -> Character:
        pass

    @abstractmethod
    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        pass

    @abstractmethod
    def get_characters_by_owner(self, owner_username: str) -> List[Character]:
        pass

    @abstractmethod
    def update_character_status(self, character_id: int, is_alive: bool) -> Optional[Character]:
        pass

    @abstractmethod
    def assign_character_to_match(self, character_id: int, match_id: int) -> Optional[Character]:
        pass

class MatchRepo(BaseRepo):
    @abstractmethod
    def create_match(self, entry_fee: float, kill_award_rate: float, start_method: str, start_threshold: int) -> Match:
        pass

    @abstractmethod
    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        pass

    @abstractmethod
    def update_match_status(self, match_id: int, status: str) -> Optional[Match]:
        pass

    @abstractmethod
    def set_match_start_time(self, match_id: int) -> Optional[Match]:
        pass

    @abstractmethod
    def set_match_end_time(self, match_id: int) -> Optional[Match]:
        pass

    @abstractmethod
    def set_match_winner(self, match_id: int, winner_character_id: int) -> Optional[Match]:
        pass

class EventRepo(BaseRepo):
    @abstractmethod
    def create_match_event(self, match_id: int, round_number: int, event_type: str, scenario_source: str, scenario_text: str, affected_character_ids: str) -> MatchEvent:
        pass

    @abstractmethod
    def get_events_for_match(self, match_id: int) -> List[MatchEvent]:
        pass

class ItemRepo(BaseRepo):
    @abstractmethod
    def get_item_by_name(self, name: str) -> Optional[Item]:
        pass

    @abstractmethod
    def create_item(self, name: str, type: str, rarity: str, description: str = None, on_find: str = None, on_award: str = None) -> Item:
        pass

    @abstractmethod
    def get_all_items(self) -> List[Item]:
        pass

# --- SQLite Implementations ---

class SqlPlayerRepo(PlayerRepo):
    def get_player_by_username(self, username: str) -> Optional[Player]:
        return self.db.query(Player).filter(Player.username == username).first()

    def create_player(self, username: str) -> Player:
        db_player = Player(username=username)
        self.db.add(db_player)
        self.db.flush()
        return db_player

    def get_or_create_player(self, username: str) -> Player:
        player = self.get_player_by_username(username)
        if not player:
            player = self.create_player(username)
        return player

    def update_player_balance(self, player_id: int, amount_change: float) -> Optional[Player]:
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if player:
            player.balance += amount_change
        return player

    def add_win(self, player_id: int) -> Optional[Player]:
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if player:
            player.wins += 1
        return player

    def add_kill(self, player_id: int) -> Optional[Player]:
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if player:
            player.kills += 1
        return player

    def add_sui_earned(self, player_id: int, amount: float) -> Optional[Player]:
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if player:
            player.total_sui_earned += amount
        return player

    def get_player_inventory(self, player_id: int) -> List[PlayerItem]:
        return self.db.query(PlayerItem).filter(PlayerItem.player_id == player_id).all()

    def add_item_to_inventory(self, player_id: int, item_id: int, quantity: int = 1) -> Optional[PlayerItem]:
        player_item = self.db.query(PlayerItem).filter(PlayerItem.player_id == player_id, PlayerItem.item_id == item_id).first()
        if player_item:
            player_item.quantity += quantity
        else:
            player_item = PlayerItem(player_id=player_id, item_id=item_id, quantity=quantity)
            self.db.add(player_item)
            self.db.flush()
        return player_item

    def get_all_players(self, limit: int = 100) -> List[Player]:
        return self.db.query(Player).limit(limit).all()

class SqlCharacterRepo(CharacterRepo):
    def create_character(self, name: str, owner_username: str) -> Character:
        db_character = Character(name=name, owner_username=owner_username)
        self.db.add(db_character)
        self.db.flush()
        return db_character

    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        return self.db.query(Character).filter(Character.id == character_id).first()

    def get_characters_by_owner(self, owner_username: str) -> List[Character]:
        return self.db.query(Character).filter(Character.owner_username == owner_username).all()

    def update_character_status(self, character_id: int, is_alive: bool) -> Optional[Character]:
        character = self.get_character_by_id(character_id)
        if character:
            character.is_alive = 1 if is_alive else 0
        return character

    def assign_character_to_match(self, character_id: int, match_id: int) -> Optional[Character]:
        character = self.get_character_by_id(character_id)
        if character:
            character.match_id = match_id
        return character

class SqlMatchRepo(MatchRepo):
    def create_match(self, entry_fee: float, kill_award_rate: float, start_method: str, start_threshold: int) -> Match:
        db_match = Match(
            entry_fee=entry_fee,
            kill_award_rate=kill_award_rate,
            start_method=start_method,
            start_threshold=start_threshold,
            status="pending"
        )
        self.db.add(db_match)
        self.db.flush()
        return db_match

    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        return self.db.query(Match).filter(Match.id == match_id).first()

    def update_match_status(self, match_id: int, status: str) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.status = status
        return match

    def set_match_start_time(self, match_id: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.start_timestamp = datetime.datetime.now(datetime.timezone.utc)
        return match

    def set_match_end_time(self, match_id: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.end_timestamp = datetime.datetime.now(datetime.timezone.utc)
        return match

    def set_match_winner(self, match_id: int, winner_character_id: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.winner_character_id = winner_character_id
        return match

class SqlEventRepo(EventRepo):
    def create_match_event(self, match_id: int, round_number: int, event_type: str, scenario_source: str, scenario_text: str, affected_character_ids: str) -> MatchEvent:
        db_event = MatchEvent(
            match_id=match_id,
            round_number=round_number,
            event_type=event_type,
            scenario_source=scenario_source,
            scenario_text=scenario_text,
            affected_character_ids=affected_character_ids
        )
        self.db.add(db_event)
        self.db.flush()
        return db_event

    def get_events_for_match(self, match_id: int) -> List[MatchEvent]:
        return self.db.query(MatchEvent).filter(MatchEvent.match_id == match_id).order_by(MatchEvent.timestamp).all()

class SqlItemRepo(ItemRepo):
    def get_item_by_name(self, name: str) -> Optional[Item]:
        return self.db.query(Item).filter(Item.name == name).first()

    def create_item(self, name: str, type: str, rarity: str, description: str = None, on_find: str = None, on_award: str = None) -> Item:
        db_item = Item(
            name=name,
            type=type,
            rarity=rarity,
            description=description,
            on_find_hook_info=on_find,
            on_award_hook_info=on_award
        )
        self.db.add(db_item)
        self.db.flush()
        return db_item

    def get_all_items(self) -> List[Item]:
        return self.db.query(Item).all()

# Dependency function for getting DB session (e.g. in FastAPI)
def get_db():
    """
    Yields a transactional session: commits on success, rolls back on error,
    and always closes the session.
    """
    with get_session() as session:
        yield session

