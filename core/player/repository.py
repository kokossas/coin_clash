"""
Player repository implementation for database operations related to players.
"""

from typing import List, Optional

from abc import abstractmethod

from ..common.repository import BaseRepo
from backend.app.models.models import Player, PlayerItem

class PlayerRepo(BaseRepo):
    """Repository interface for player operations."""
    
    @abstractmethod
    def get_player_by_username(self, username: str) -> Optional[Player]:
        pass

    @abstractmethod
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        pass

    @abstractmethod
    def get_player_by_wallet_address(self, wallet_address: str) -> Optional[Player]:
        pass

    @abstractmethod
    def create_player(self, wallet_address: str, username: Optional[str] = None) -> Player:
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
    def add_earnings(self, player_id: int, amount: float) -> Optional[Player]:
        pass

    @abstractmethod
    def get_player_inventory(self, player_id: int) -> List[PlayerItem]:
        pass

    @abstractmethod
    def add_item_to_inventory(self, player_id: int, item_id: int, quantity: int = 1) -> Optional[PlayerItem]:
        pass
        
    @abstractmethod
    def get_or_create_player(self, wallet_address: str, username: Optional[str] = None) -> Player:
        pass
        
    @abstractmethod
    def get_all_players(self, limit: int = 100) -> List[Player]:
        pass


class SqlPlayerRepo(PlayerRepo):
    """SQL implementation of PlayerRepo interface."""
    
    def get_player_by_username(self, username: str) -> Optional[Player]:
        return self.db.query(Player).filter(Player.username == username).first()

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        return self.db.query(Player).filter(Player.id == player_id).first()

    def get_player_by_wallet_address(self, wallet_address: str) -> Optional[Player]:
        return self.db.query(Player).filter(Player.wallet_address == wallet_address).first()

    def create_player(self, wallet_address: str, username: Optional[str] = None) -> Player:
        display_name = username or f"Player_{wallet_address[:6]}"
        db_player = Player(wallet_address=wallet_address, username=display_name)
        self.db.add(db_player)
        self.db.flush()
        return db_player

    def get_or_create_player(self, wallet_address: str, username: Optional[str] = None) -> Player:
        player = self.get_player_by_wallet_address(wallet_address)
        if not player:
            player = self.create_player(wallet_address, username)
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

    def add_earnings(self, player_id: int, amount: float) -> Optional[Player]:
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if player:
            player.total_earnings += amount
        return player

    def get_player_inventory(self, player_id: int) -> List[PlayerItem]:
        return self.db.query(PlayerItem).filter(PlayerItem.player_id == player_id).all()

    def add_item_to_inventory(self, player_id: int, item_id: int, quantity: int = 1) -> Optional[PlayerItem]:
        player_item = self.db.query(PlayerItem).filter(
            PlayerItem.player_id == player_id, 
            PlayerItem.item_id == item_id
        ).first()
        
        if player_item:
            player_item.quantity += quantity
        else:
            player_item = PlayerItem(player_id=player_id, item_id=item_id, quantity=quantity)
            self.db.add(player_item)
            self.db.flush()
        return player_item

    def get_all_players(self, limit: int = 100) -> List[Player]:
        return self.db.query(Player).limit(limit).all()
