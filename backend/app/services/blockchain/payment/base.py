from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class PaymentProvider(ABC):
    """
    Abstract payment provider interface.
    This interface can be implemented by both traditional and blockchain-based payment providers.
    """
    
    @abstractmethod
    async def process_deposit(self, wallet_address: str, amount: float, currency: str) -> Dict:
        """
        Process a deposit from a wallet.
        
        Args:
            wallet_address: The blockchain wallet address making the deposit
            amount: The amount to deposit
            currency: The currency code (e.g., "SUI", "MATIC")
            
        Returns:
            Dict containing transaction details including:
            - success: Boolean indicating if the deposit was successful
            - transaction_id: Unique identifier for the transaction
            - status: Current status of the transaction
            - amount: The amount deposited
            - currency: The currency of the deposit
        """
        pass
    
    @abstractmethod
    async def process_withdrawal(self, wallet_address: str, amount: float, currency: str) -> Dict:
        """
        Process a withdrawal to a wallet.
        
        Args:
            wallet_address: The blockchain wallet address receiving the withdrawal
            amount: The amount to withdraw
            currency: The currency code (e.g., "SUI", "MATIC")
            
        Returns:
            Dict containing transaction details including:
            - success: Boolean indicating if the withdrawal was successful
            - transaction_id: Unique identifier for the transaction
            - status: Current status of the transaction
            - amount: The amount withdrawn
            - currency: The currency of the withdrawal
        """
        pass
    
    @abstractmethod
    async def get_balance(self, wallet_address: str, currency: str) -> float:
        """
        Get the balance for a wallet.
        
        Args:
            wallet_address: The blockchain wallet address to check
            currency: The currency code (e.g., "SUI", "MATIC")
            
        Returns:
            The current balance as a float
        """
        pass
    
    @abstractmethod
    async def estimate_fees(self, amount: float, currency: str) -> Dict:
        """
        Estimate transaction fees.
        
        Args:
            amount: The transaction amount
            currency: The currency code (e.g., "SUI", "MATIC")
            
        Returns:
            Dict containing fee details including:
            - fee_amount: The estimated fee amount
            - fee_currency: The currency of the fee
            - gas_price: The current gas price (if applicable)
            - gas_limit: The estimated gas limit (if applicable)
        """
        pass
