from typing import Dict, List, Optional
import uuid
from datetime import datetime
from ..errors import TemporaryBlockchainError, PermanentBlockchainError
from .base import PaymentProvider

class MockPaymentProvider(PaymentProvider):
    def __init__(self):
        self._balances = {}
        self._transactions = {}
        self.simulated_delay = 0.5
        self.failure_rate = 0.0
    
    async def process_deposit(self, wallet_address: str, amount: float, currency: str) -> Dict:
        await self._simulate_delay()
        
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while processing deposit for {wallet_address}")
        
        if amount <= 0:
            raise PermanentBlockchainError("Deposit amount must be greater than zero")
        
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        self._ensure_balance_exists(wallet_address, currency)
        
        tx_id = f"mock-deposit-{uuid.uuid4()}"
        self._balances[wallet_address][currency] += amount
        
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
        await self._simulate_delay()
        
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while processing withdrawal for {wallet_address}")
        
        if amount <= 0:
            raise PermanentBlockchainError("Withdrawal amount must be greater than zero")
        
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        self._ensure_balance_exists(wallet_address, currency)
        
        if self._balances[wallet_address][currency] < amount:
            raise PermanentBlockchainError(f"Insufficient balance for withdrawal: {self._balances[wallet_address][currency]} {currency} available")
        
        tx_id = f"mock-withdrawal-{uuid.uuid4()}"
        self._balances[wallet_address][currency] -= amount
        
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
        await self._simulate_delay()
        
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        self._ensure_balance_exists(wallet_address, currency)
        
        return self._balances[wallet_address][currency]
    
    async def estimate_fees(self, amount: float, currency: str) -> Dict:
        await self._simulate_delay()
        
        if self._should_fail():
            raise TemporaryBlockchainError("Network error while estimating fees")
        
        fee_amount = amount * 0.001
        
        return {
            "fee_amount": fee_amount,
            "fee_currency": currency,
            "gas_price": 50,
            "gas_limit": 21000
        }
    
    def _ensure_balance_exists(self, wallet_address: str, currency: str) -> None:
        if wallet_address not in self._balances:
            self._balances[wallet_address] = {}
        
        if currency not in self._balances[wallet_address]:
            self._balances[wallet_address][currency] = 0.0
    
    async def _simulate_delay(self) -> None:
        if self.simulated_delay > 0:
            import asyncio
            await asyncio.sleep(self.simulated_delay)
    
    def _should_fail(self) -> bool:
        if self.failure_rate <= 0:
            return False
        
        import random
        return random.random() < self.failure_rate
    
    def set_balance(self, wallet_address: str, currency: str, amount: float) -> None:
        self._ensure_balance_exists(wallet_address, currency)
        self._balances[wallet_address][currency] = amount
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        return self._transactions.get(transaction_id)
    
    def get_all_transactions(self, wallet_address: str = None) -> List[Dict]:
        if wallet_address:
            return [tx for tx in self._transactions.values() if tx["wallet_address"] == wallet_address]
        return list(self._transactions.values())
