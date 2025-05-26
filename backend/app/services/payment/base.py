from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

class PaymentProvider(ABC):
    """
    Abstract payment provider interface for future blockchain integration.
    This interface can be implemented by both traditional and blockchain payment providers.
    """
    
    @abstractmethod
    async def process_deposit(self, player_id: int, amount: float, currency: str) -> Dict[str, Any]:
        """Process a deposit from a player."""
        pass
    
    @abstractmethod
    async def process_withdrawal(self, player_id: int, amount: float, currency: str) -> Dict[str, Any]:
        """Process a withdrawal to a player."""
        pass
    
    @abstractmethod
    async def get_balance(self, player_id: int, currency: str) -> float:
        """Get the balance for a player."""
        pass
    
    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get the status of a transaction."""
        pass
