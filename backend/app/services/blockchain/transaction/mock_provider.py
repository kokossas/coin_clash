from typing import Dict, List
import uuid
from datetime import datetime
from ..errors import TemporaryBlockchainError, PermanentBlockchainError
from .base import TransactionProvider

class MockTransactionProvider(TransactionProvider):
    """
    Mock transaction provider for testing and development.
    This implementation simulates blockchain transactions without actual blockchain interactions.
    """
    
    def __init__(self):
        # In-memory storage for transactions
        self._transactions = {}
        # Configurable delay to simulate network latency (in seconds)
        self.simulated_delay = 0.5
        # Configurable failure rate (0.0 to 1.0)
        self.failure_rate = 0.0
        # Configurable confirmation time (in seconds)
        self.confirmation_time = 2.0
    
    async def create_transaction(self, from_address: str, to_address: str, amount: float, currency: str) -> Dict:
        """Create a new blockchain transaction."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while creating transaction from {from_address} to {to_address}")
        
        # Validate inputs
        if amount <= 0:
            raise PermanentBlockchainError("Transaction amount must be greater than zero")
        
        if not from_address or not to_address:
            raise PermanentBlockchainError("Both sender and recipient addresses are required")
        
        # Create transaction ID
        tx_id = f"mock-tx-{uuid.uuid4()}"
        
        # Record transaction
        timestamp = datetime.now().isoformat()
        transaction = {
            "transaction_id": tx_id,
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
            "currency": currency,
            "status": "pending",
            "confirmations": 0,
            "block_number": None,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        self._transactions[tx_id] = transaction
        
        # Schedule confirmation (in a real implementation, this would be handled by a background task)
        self._schedule_confirmation(tx_id)
        
        return {
            "transaction_id": tx_id,
            "status": "pending",
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
            "currency": currency,
            "timestamp": timestamp
        }
    
    async def get_transaction_status(self, transaction_id: str) -> Dict:
        """Get the status of a transaction."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Check if transaction exists
        if transaction_id not in self._transactions:
            raise PermanentBlockchainError(f"Transaction not found: {transaction_id}")
        
        transaction = self._transactions[transaction_id]
        
        return {
            "transaction_id": transaction_id,
            "status": transaction["status"],
            "confirmations": transaction["confirmations"],
            "block_number": transaction["block_number"],
            "timestamp": transaction["updated_at"]
        }
    
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict]:
        """Get transaction history for a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Find transactions involving the wallet
        transactions = []
        for tx in self._transactions.values():
            if tx["from_address"] == wallet_address or tx["to_address"] == wallet_address:
                transactions.append({
                    "transaction_id": tx["transaction_id"],
                    "status": tx["status"],
                    "from_address": tx["from_address"],
                    "to_address": tx["to_address"],
                    "amount": tx["amount"],
                    "currency": tx["currency"],
                    "timestamp": tx["created_at"]
                })
        
        # Sort by timestamp (newest first) and apply limit
        transactions.sort(key=lambda tx: tx["timestamp"], reverse=True)
        return transactions[:limit]
    
    async def retry_transaction(self, transaction_id: str) -> Dict:
        """Retry a failed transaction."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Check if transaction exists
        if transaction_id not in self._transactions:
            raise PermanentBlockchainError(f"Transaction not found: {transaction_id}")
        
        original_tx = self._transactions[transaction_id]
        
        # Check if transaction can be retried
        if original_tx["status"] != "failed":
            raise PermanentBlockchainError(f"Only failed transactions can be retried. Current status: {original_tx['status']}")
        
        # Create new transaction ID
        new_tx_id = f"mock-retry-{uuid.uuid4()}"
        
        # Record new transaction
        timestamp = datetime.now().isoformat()
        new_transaction = {
            "transaction_id": new_tx_id,
            "from_address": original_tx["from_address"],
            "to_address": original_tx["to_address"],
            "amount": original_tx["amount"],
            "currency": original_tx["currency"],
            "status": "pending",
            "confirmations": 0,
            "block_number": None,
            "created_at": timestamp,
            "updated_at": timestamp,
            "original_transaction_id": transaction_id
        }
        self._transactions[new_tx_id] = new_transaction
        
        # Schedule confirmation
        self._schedule_confirmation(new_tx_id)
        
        return {
            "transaction_id": new_tx_id,
            "status": "pending",
            "original_transaction_id": transaction_id,
            "timestamp": timestamp
        }
    
    # Helper methods
    
    async def _simulate_delay(self) -> None:
        """Simulate network delay."""
        if self.simulated_delay > 0:
            import asyncio
            await asyncio.sleep(self.simulated_delay)
    
    def _should_fail(self) -> bool:
        """Determine if an operation should fail based on the failure rate."""
        if self.failure_rate <= 0:
            return False
        
        import random
        return random.random() < self.failure_rate
    
    def _schedule_confirmation(self, transaction_id: str) -> None:
        """
        Schedule a transaction confirmation.
        
        In a real implementation, this would be handled by a background task or webhook.
        For this mock implementation, we'll use a simple async task.
        """
        import asyncio
        
        async def confirm_after_delay():
            await asyncio.sleep(self.confirmation_time)
            
            # Simulate random failures during confirmation
            if self._should_fail():
                self._transactions[transaction_id]["status"] = "failed"
            else:
                self._transactions[transaction_id]["status"] = "confirmed"
                self._transactions[transaction_id]["confirmations"] = 1
                self._transactions[transaction_id]["block_number"] = 12345678  # Mock block number
            
            self._transactions[transaction_id]["updated_at"] = datetime.now().isoformat()
        
        # Start the confirmation task (in a real implementation, this would be more robust)
        asyncio.create_task(confirm_after_delay())
    
    # Additional methods for testing and simulation
    
    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions for testing purposes."""
        return list(self._transactions.values())
    
    def set_transaction_status(self, transaction_id: str, status: str) -> None:
        """Manually set a transaction status for testing purposes."""
        if transaction_id in self._transactions:
            self._transactions[transaction_id]["status"] = status
            self._transactions[transaction_id]["updated_at"] = datetime.now().isoformat()
            
            if status == "confirmed":
                self._transactions[transaction_id]["confirmations"] = 1
                self._transactions[transaction_id]["block_number"] = 12345678  # Mock block number
