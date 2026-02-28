from abc import ABC, abstractmethod
from typing import Dict, List

class TransactionProvider(ABC):
    """
    Abstract transaction provider interface.
    This interface can be implemented by both traditional and blockchain-based transaction providers.
    """
    
    @abstractmethod
    async def create_transaction(self, from_address: str, to_address: str, amount: float, currency: str) -> Dict:
        """
        Create a new blockchain transaction.
        
        Args:
            from_address: The sender's blockchain wallet address
            to_address: The recipient's blockchain wallet address
            amount: The amount to transfer
            currency: The currency code (e.g., "SUI", "MATIC")
            
        Returns:
            Dict containing transaction details including:
            - transaction_id: Unique identifier for the transaction
            - status: Current status of the transaction
            - from_address: The sender's address
            - to_address: The recipient's address
            - amount: The transaction amount
            - currency: The transaction currency
            - timestamp: When the transaction was created
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> Dict:
        """
        Get the status of a transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            
        Returns:
            Dict containing status details including:
            - transaction_id: Unique identifier for the transaction
            - status: Current status (e.g., "pending", "confirmed", "failed")
            - confirmations: Number of confirmations (if applicable)
            - block_number: Block number containing the transaction (if confirmed)
            - timestamp: When the status was last updated
        """
        pass
    
    @abstractmethod
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict]:
        """
        Get transaction history for a wallet.
        
        Args:
            wallet_address: The blockchain wallet address
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries, each containing:
            - transaction_id: Unique identifier for the transaction
            - status: Current status of the transaction
            - from_address: The sender's address
            - to_address: The recipient's address
            - amount: The transaction amount
            - currency: The transaction currency
            - timestamp: When the transaction was created
        """
        pass
    
    @abstractmethod
    async def retry_transaction(self, transaction_id: str) -> Dict:
        """
        Retry a failed transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            
        Returns:
            Dict containing updated transaction details including:
            - transaction_id: Unique identifier for the transaction (may be new)
            - status: Current status of the transaction
            - original_transaction_id: The ID of the original failed transaction
            - timestamp: When the retry was attempted
        """
        pass
