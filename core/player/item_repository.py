"""
Item repository implementation for database operations related to items.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..common.repository import BaseRepo
from ..database.models import Item

class ItemRepo(BaseRepo):
    """Repository interface for item operations."""
    
    def get_item_by_name(self, name: str) -> Optional[Item]:
        """
        Get an item by name.
        
        Args:
            name: The item's name
            
        Returns:
            Item object if found, None otherwise
        """
        pass

    def create_item(self, name: str, type: str, rarity: str, description: str = None, on_find: str = None, on_award: str = None) -> Item:
        """
        Create a new item.
        
        Args:
            name: The item's name
            type: Type of item (e.g., "cosmetic", "gear")
            rarity: Rarity of the item (e.g., "common", "rare")
            description: Description of the item (optional)
            on_find: Hook information for when item is found (optional)
            on_award: Hook information for when item is awarded (optional)
            
        Returns:
            The created Item object
        """
        pass

    def get_all_items(self) -> List[Item]:
        """
        Get all items.
        
        Returns:
            List of all Item objects
        """
        pass


class SqlItemRepo(ItemRepo):
    """SQL implementation of ItemRepo interface."""
    
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
