from typing import Dict, List
import uuid
from datetime import datetime
from ..errors import TemporaryBlockchainError, PermanentBlockchainError
from .base import WalletProvider

class MockWalletProvider(WalletProvider):
    def __init__(self):
        self._connected_wallets = {}
        self._valid_signatures = {}
        self.simulated_delay = 0.5
        self.failure_rate = 0.0
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
        await self._simulate_delay()
        
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while connecting to wallet {wallet_address}")
        
        if not wallet_address:
            raise PermanentBlockchainError("Wallet address is required")
        
        valid_chain = False
        for chain in self._supported_chains:
            if chain["chain_id"] == chain_id:
                valid_chain = True
                break
        
        if not valid_chain:
            raise PermanentBlockchainError(f"Unsupported chain ID: {chain_id}")
        
        connection_id = f"mock-connection-{uuid.uuid4()}"
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
        await self._simulate_delay()
        
        if wallet_address not in self._connected_wallets:
            return {
                "success": False,
                "wallet_address": wallet_address,
                "error": "Wallet not connected"
            }
        
        del self._connected_wallets[wallet_address]
        
        return {
            "success": True,
            "wallet_address": wallet_address
        }

    async def verify_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        await self._simulate_delay()
        
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while verifying signature for wallet {wallet_address}")
        
        if not wallet_address or not message or not signature:
            raise PermanentBlockchainError("Wallet address, message, and signature are required")
        
        signature_key = f"{wallet_address}:{message}"
        
        if signature_key in self._valid_signatures:
            return self._valid_signatures[signature_key] == signature
        
        is_valid = len(signature) > 10 and signature.startswith("0x")
        
        if is_valid:
            self._valid_signatures[signature_key] = signature
        
        return is_valid
    
    async def get_supported_chains(self) -> List[Dict]:
        await self._simulate_delay()
        return self._supported_chains
    
    async def _simulate_delay(self) -> None:
        if self.simulated_delay > 0:
            import asyncio
            await asyncio.sleep(self.simulated_delay)
    
    def _should_fail(self) -> bool:
        if self.failure_rate <= 0:
            return False
        
        import random
        return random.random() < self.failure_rate
    
    def get_connected_wallets(self) -> List[Dict]:
        return list(self._connected_wallets.values())
    
    def add_supported_chain(self, chain_id: str, name: str, currency: str, is_testnet: bool) -> None:
        self._supported_chains.append({
            "chain_id": chain_id,
            "name": name,
            "currency": currency,
            "is_testnet": is_testnet
        })
    
    def register_valid_signature(self, wallet_address: str, message: str, signature: str) -> None:
        signature_key = f"{wallet_address}:{message}"
        self._valid_signatures[signature_key] = signature
