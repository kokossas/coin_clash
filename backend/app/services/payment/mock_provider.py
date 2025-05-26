from typing import Dict, Any
from .base import PaymentProvider

class MockPaymentProvider(PaymentProvider):
    """
    Mock payment provider for testing and development.
    This implementation simulates payment processing without actual transactions.
    """
    
    async def process_deposit(self, player_id: int, amount: float, currency: str) -> Dict[str, Any]:
        """Process a deposit from a player."""
        return {
            "success": True,
            "transaction_id": f"mock-deposit-{player_id}-{amount}",
            "status": "completed",
            "amount": amount,
            "currency": currency
        }
    
    async def process_withdrawal(self, player_id: int, amount: float, currency: str) -> Dict[str, Any]:
        """Process a withdrawal to a player."""
        return {
            "success": True,
            "transaction_id": f"mock-withdrawal-{player_id}-{amount}",
            "status": "completed",
            "amount": amount,
            "currency": currency
        }
    
    async def get_balance(self, player_id: int, currency: str) -> float:
        """Get the balance for a player."""
        # In a real implementation, this would query the payment provider
        # For mock purposes, we'll return a fixed value
        return 100.0
    
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get the status of a transaction."""
        return {
            "transaction_id": transaction_id,
            "status": "completed"
        }
