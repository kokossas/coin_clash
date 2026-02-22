"""
Player repository implementation for database operations related to players.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..common.repository import BaseRepo
from backend.app.models.models import Player, PlayerItem

class PlayerRepo(BaseRepo):
    """Repository interface for player operations."""
    
    def get_player_by_username(self, username: str) -> Optional[Player]:
        """
        Get a player by their username.
        
        Args:
            username: The player's username
            
        Returns:
            Player object if found, None otherwise
        """
        pass

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Get a player by their ID.
        
        Args:
            player_id: The player's internal PK
            
        Returns:
            Player object if found, None otherwise
        """
        pass

    def create_player(self, username: str) -> Player:
        """
        Create a new player.
        
        Args:
            username: The player's username
            
        Returns:
            The created Player object
        """
        pass

    def update_player_balance(self, player_id: int, amount_change: float) -> Optional[Player]:
        """
        Update a player's balance.
        
        Args:
            player_id: The player's ID
            amount_change: Amount to add to balance (negative for deduction)
            
        Returns:
            Updated Player object if found, None otherwise
        """
        pass

    def add_win(self, player_id: int) -> Optional[Player]:
        """
        Increment a player's win count.
        
        Args:
            player_id: The player's ID
            
        Returns:
            Updated Player object if found, None otherwise
        """
        pass

    def add_kill(self, player_id: int) -> Optional[Player]:
        """
        Increment a player's kill count.
        
        Args:
            player_id: The player's ID
            
        Returns:
            Updated Player object if found, None otherwise
        """
        pass

    def add_sui_earned(self, player_id: int, amount: float) -> Optional[Player]:
        """
        Add to a player's total SUI earned.
        
        Args:
            player_id: The player's ID
            amount: Amount of SUI earned
            
        Returns:
            Updated Player object if found, None otherwise
        """
        pass

    def get_player_inventory(self, player_id: int) -> List[PlayerItem]:
        """
        Get a player's inventory items.
        
        Args:
            player_id: The player's ID
            
        Returns:
            List of PlayerItem objects
        """
        pass

    def add_item_to_inventory(self, player_id: int, item_id: int, quantity: int = 1) -> Optional[PlayerItem]:
        """
        Add an item to a player's inventory.
        
        Args:
            player_id: The player's ID
            item_id: The item's ID
            quantity: Quantity to add (default: 1)
            
        Returns:
            Updated or created PlayerItem object if successful, None otherwise
        """
        pass
        
    def get_or_create_player(self, username: str) -> Player:
        """
        Get a player by username or create if not exists.
        
        Args:
            username: The player's username
            
        Returns:
            Existing or newly created Player object
        """
        pass
        
    def get_all_players(self, limit: int = 100) -> List[Player]:
        """
        Get all players up to a limit.
        
        Args:
            limit: Maximum number of players to return (default: 100)
            
        Returns:
            List of Player objects
        """
        pass


class SqlPlayerRepo(PlayerRepo):
    """SQL implementation of PlayerRepo interface."""
    
    def get_player_by_username(self, username: str) -> Optional[Player]:
        return self.db.query(Player).filter(Player.username == username).first()

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        return self.db.query(Player).filter(Player.id == player_id).first()

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
