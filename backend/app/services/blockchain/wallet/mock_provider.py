from typing import Dict, List
import uuid
from datetime import datetime
from ..errors import TemporaryBlockchainError, PermanentBlockchainError
from .base import WalletProvider

class MockWalletProvider(WalletProvider):
    """
    Mock wallet provider for testing and development.
    This implementation simulates blockchain wallet interactions without actual blockchain connections.
    """
    
    def __init__(self):
        # In-memory storage for connected wallets
        self._connected_wallets = {}
        # In-memory storage for valid signatures
        self._valid_signatures = {}
        # Configurable delay to simulate network latency (in seconds)
        self.simulated_delay = 0.5
        # Configurable failure rate (0.0 to 1.0)
        self.failure_rate = 0.0
        # Supported chains
        self._supported_chains = [
            {
                "chain_id": "polygon-1",
                "name": "Polygon Mainnet",
                "currency": "MATIC",
                "is_testnet": False
            },
            {
                "chain_id": "polygon-80001",
                "name": "Polygon Mumbai Testnet",
                "currency": "MATIC",
                "is_testnet": True
            },
            {
                "chain_id": "solana-1",
                "name": "Solana Mainnet",
                "currency": "SOL",
                "is_testnet": False
            },
            {
                "chain_id": "solana-devnet",
                "name": "Solana Devnet",
                "currency": "SOL",
                "is_testnet": True
            }
        ]
    
    async def connect_wallet(self, wallet_address: str, chain_id: str) -> Dict:
        """Connect to a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while connecting to wallet {wallet_address}")
        
        # Validate inputs
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        # Validate chain ID
        valid_chain = False
        for chain in self._supported_chains:
            if chain["chain_id"] == chain_id:
                valid_chain = True
                break
        
        if not valid_chain:
            raise PermanentBlockchainError(f"Unsupported chain ID: {chain_id}")
        
        # Create connection ID
        connection_id = f"mock-connection-{uuid.uuid4()}"
        
        # Record connection
        timestamp = datetime.now().isoformat()
        connection = {
            "connection_id": connection_id,
            "wallet_address": wallet_address,
            "chain_id": chain_id,
            "connected_at": timestamp,
            "status": "connected"
        }
        self._connected_wallets[wallet_address] = connection
        
        return {
            "success": True,
            "wallet_address": wallet_address,
            "chain_id": chain_id,
            "connection_id": connection_id
        }
    
    async def disconnect_wallet(self, wallet_address: str) -> Dict:
        """Disconnect from a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Check if wallet is connected
        if wallet_address not in self._connected_wallets:
            return {
                "success": False,
                "wallet_address": wallet_address,
                "error": "Wallet not connected"
            }
        
        # Remove connection
        del self._connected_wallets[wallet_address]
        
        return {
            "success": True,
            "wallet_address": wallet_address
        }
    
    async def verify_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        """Verify a signature from a wallet."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while verifying signature for wallet {wallet_address}")
        
        # Validate inputs
        if not wallet_address or not message or not signature:
            raise PermanentBlockchainError("Wallet address, message, and signature are required")
        
        # In a real implementation, this would verify the signature cryptographically
        # For this mock implementation, we'll use a simple key
        signature_key = f"{wallet_address}:{message}"
        
        # Check if this is a signature we've seen before
        if signature_key in self._valid_signatures:
            return self._valid_signatures[signature_key] == signature
        
        # For new signatures, we'll consider them valid if they meet a simple pattern
        # In a real implementation, this would be actual cryptographic verification
        is_valid = len(signature) > 10 and signature.startswith("0x")
        
        # Store the result for future checks
        if is_valid:
            self._valid_signatures[signature_key] = signature
        
        return is_valid
    
    async def get_supported_chains(self) -> List[Dict]:
        """Get list of supported blockchain networks."""
        # Simulate network delay
        await self._simulate_delay()
        
        return self._supported_chains
    
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
    
    # Additional methods for testing and simulation
    
    def get_connected_wallets(self) -> List[Dict]:
        """Get all connected wallets for testing purposes."""
        return list(self._connected_wallets.values())
    
    def add_supported_chain(self, chain_id: str, name: str, currency: str, is_testnet: bool) -> None:
        """Add a new supported chain for testing purposes."""
        self._supported_chains.append({
            "chain_id": chain_id,
            "name": name,
            "currency": currency,
            "is_testnet": is_testnet
        })
    
    def register_valid_signature(self, wallet_address: str, message: str, signature: str) -> None:
        """Register a valid signature for testing purposes."""
        signature_key = f"{wallet_address}:{message}"
        self._valid_signatures[signature_key] = signature
