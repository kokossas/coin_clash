from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import Player
from ..schemas.player import PlayerCreate, PlayerUpdate

class CRUDPlayer(CRUDBase[Player, PlayerCreate, PlayerUpdate]):
    """CRUD operations for Player model"""

    def get_by_username(self, db: Session, username: str) -> Optional[Player]:
        return db.query(Player).filter(Player.username == username).first()

    def get_by_wallet_address(self, db: Session, wallet_address: str) -> Optional[Player]:
        return db.query(Player).filter(Player.wallet_address == wallet_address).first()

    def create(self, db: Session, *, obj_in: PlayerCreate) -> Player:
        username = obj_in.username or f"Player_{obj_in.wallet_address[:6]}"
        db_obj = Player(wallet_address=obj_in.wallet_address, username=username)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_player_balance(self, db: Session, player_id: int, amount: float) -> Optional[Player]:
        player = self.get(db, player_id)
        if player:
            player.balance += amount
            db.add(player)
            db.commit()
            db.refresh(player)
        return player

    def add_win(self, db: Session, player_id: int) -> Optional[Player]:
        player = self.get(db, player_id)
        if player:
            player.wins += 1
            db.add(player)
            db.commit()
            db.refresh(player)
        return player

    def add_kill(self, db: Session, player_id: int) -> Optional[Player]:
        player = self.get(db, player_id)
        if player:
            player.kills += 1
            db.add(player)
            db.commit()
            db.refresh(player)
        return player

crud_player = CRUDPlayer(Player)
