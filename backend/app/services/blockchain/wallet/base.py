from abc import ABC, abstractmethod
from typing import Dict, List

class WalletProvider(ABC):
    """
    Abstract wallet provider interface.
    This interface can be implemented by both traditional and blockchain-based wallet providers.
    """
    
    @abstractmethod
    async def connect_wallet(self, wallet_address: str, chain_id: str) -> Dict:
        """
        Connect to a wallet.
        
        Args:
            wallet_address: The blockchain wallet address to connect
            chain_id: The blockchain network identifier
            
        Returns:
            Dict containing connection details including:
            - success: Boolean indicating if the connection was successful
            - wallet_address: The connected wallet address
            - chain_id: The connected blockchain network
            - connection_id: Unique identifier for this connection session
        """
        pass
    
    @abstractmethod
    async def disconnect_wallet(self, wallet_address: str) -> Dict:
        """
        Disconnect from a wallet.
        
        Args:
            wallet_address: The blockchain wallet address to disconnect
            
        Returns:
            Dict containing disconnection details including:
            - success: Boolean indicating if the disconnection was successful
            - wallet_address: The disconnected wallet address
        """
        pass
    
    @abstractmethod
    async def verify_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        """
        Verify a signature from a wallet.
        
        Args:
            wallet_address: The blockchain wallet address that signed the message
            message: The original message that was signed
            signature: The signature to verify
            
        Returns:
            Boolean indicating if the signature is valid
        """
        pass
    
    @abstractmethod
    async def get_supported_chains(self) -> List[Dict]:
        """
        Get list of supported blockchain networks.
        
        Returns:
            List of dictionaries, each containing:
            - chain_id: The blockchain network identifier
            - name: Human-readable name of the blockchain
            - currency: Native currency of the blockchain
            - is_testnet: Boolean indicating if this is a test network
        """
        pass
