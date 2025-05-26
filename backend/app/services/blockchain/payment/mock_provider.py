from typing import Dict, List, Optional
import uuid
import time
from datetime import datetime
from ..errors import TemporaryBlockchainError, PermanentBlockchainError
from .base import PaymentProvider

class MockPaymentProvider(PaymentProvider):
    """
    Mock payment provider for testing and development.
    This implementation simulates blockchain payment processing without actual blockchain interactions.
    """
    
    def __init__(self):
        # In-memory storage for balances
        self._balances = {}
        # In-memory storage for transactions
        self._transactions = {}
        # Configurable delay to simulate network latency (in seconds)
        self.simulated_delay = 0.5
        # Configurable failure rate (0.0 to 1.0)
        self.failure_rate = 0.0
    
    async def process_deposit(self, wallet_address: str, amount: float, currency: str) -> Dict:
        """Process a deposit from a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while processing deposit for {wallet_address}")
        
        # Validate inputs
        if amount <= 0:
            raise PermanentBlockchainError("Deposit amount must be greater than zero")
        
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        # Initialize balance if needed
        self._ensure_balance_exists(wallet_address, currency)
        
        # Create transaction ID
        tx_id = f"mock-deposit-{uuid.uuid4()}"
        
        # Update balance
        self._balances[wallet_address][currency] += amount
        
        # Record transaction
        timestamp = datetime.now().isoformat()
        transaction = {
            "transaction_id": tx_id,
            "wallet_address": wallet_address,
            "amount": amount,
            "currency": currency,
            "type": "deposit",
            "status": "completed",
            "timestamp": timestamp
        }
        self._transactions[tx_id] = transaction
        
        return {
            "success": True,
            "transaction_id": tx_id,
            "status": "completed",
            "amount": amount,
            "currency": currency,
            "timestamp": timestamp
        }
    
    async def process_withdrawal(self, wallet_address: str, amount: float, currency: str) -> Dict:
        """Process a withdrawal to a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while processing withdrawal for {wallet_address}")
        
        # Validate inputs
        if amount <= 0:
            raise PermanentBlockchainError("Withdrawal amount must be greater than zero")
        
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        # Initialize balance if needed
        self._ensure_balance_exists(wallet_address, currency)
        
        # Check sufficient balance
        if self._balances[wallet_address][currency] < amount:
            raise PermanentBlockchainError(f"Insufficient balance for withdrawal: {self._balances[wallet_address][currency]} {currency} available")
        
        # Create transaction ID
        tx_id = f"mock-withdrawal-{uuid.uuid4()}"
        
        # Update balance
        self._balances[wallet_address][currency] -= amount
        
        # Record transaction
        timestamp = datetime.now().isoformat()
        transaction = {
            "transaction_id": tx_id,
            "wallet_address": wallet_address,
            "amount": amount,
            "currency": currency,
            "type": "withdrawal",
            "status": "completed",
            "timestamp": timestamp
        }
        self._transactions[tx_id] = transaction
        
        return {
            "success": True,
            "transaction_id": tx_id,
            "status": "completed",
            "amount": amount,
            "currency": currency,
            "timestamp": timestamp
        }
    
    async def get_balance(self, wallet_address: str, currency: str) -> float:
        """Get the balance for a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Validate inputs
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        # Initialize balance if needed
        self._ensure_balance_exists(wallet_address, currency)
        
        return self._balances[wallet_address][currency]
    
    async def estimate_fees(self, amount: float, currency: str) -> Dict:
        """Estimate transaction fees."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError("Network error while estimating fees")
        
        # Mock fee calculation (0.1% of transaction amount)
        fee_amount = amount * 0.001
        
        return {
            "fee_amount": fee_amount,
            "fee_currency": currency,
            "gas_price": 50,  # Mock gas price in gwei
            "gas_limit": 21000  # Mock gas limit for a standard transaction
        }
    
    # Helper methods
    
    def _ensure_balance_exists(self, wallet_address: str, currency: str) -> None:
        """Ensure that a balance entry exists for the given wallet and currency."""
        if wallet_address not in self._balances:
            self._balances[wallet_address] = {}
        
        if currency not in self._balances[wallet_address]:
            self._balances[wallet_address][currency] = 0.0
    
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
    
    # Additional methods for testing and simulation
    
    def set_balance(self, wallet_address: str, currency: str, amount: float) -> None:
        """Set a specific balance for testing purposes."""
        self._ensure_balance_exists(wallet_address, currency)
        self._balances[wallet_address][currency] = amount
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get a specific transaction by ID."""
        return self._transactions.get(transaction_id)
    
    def get_all_transactions(self, wallet_address: str = None) -> List[Dict]:
        """Get all transactions, optionally filtered by wallet address."""
        if wallet_address:
            return [tx for tx in self._transactions.values() if tx["wallet_address"] == wallet_address]
        return list(self._transactions.values())
