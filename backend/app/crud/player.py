from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import Player
from ..schemas.player import PlayerCreate, PlayerUpdate

class CRUDPlayer(CRUDBase[Player, PlayerCreate, PlayerUpdate]):
    """CRUD operations for Player model"""
    
    def get_by_username(self, db: Session, username: str) -> Optional[Player]:
        """Get a player by username"""
        return db.query(Player).filter(Player.username == username).first()
    
    def get_or_create_player(self, db: Session, username: str) -> Player:
        """Get a player by username or create if not exists"""
        player = self.get_by_username(db, username)
        if not player:
            player_in = PlayerCreate(username=username)
            player = self.create(db, obj_in=player_in)
        return player
    
    def update_player_balance(self, db: Session, player_id: int, amount: float) -> Player:
        """Update a player's balance"""
        player = self.get(db, player_id)
        if player:
            player.balance += amount
            db.add(player)
            db.commit()
            db.refresh(player)
        return player
    
    def add_win(self, db: Session, player_id: int) -> Player:
        """Increment a player's win count"""
        player = self.get(db, player_id)
        if player:
            player.wins += 1
            db.add(player)
            db.commit()
            db.refresh(player)
        return player
    
    def add_kill(self, db: Session, player_id: int) -> Player:
        """Increment a player's kill count"""
        player = self.get(db, player_id)
        if player:
            player.kills += 1
            db.add(player)
            db.commit()
            db.refresh(player)
        return player

crud_player = CRUDPlayer(Player)
