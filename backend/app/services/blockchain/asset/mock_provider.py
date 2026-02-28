from typing import Dict, List
import uuid
from datetime import datetime
from ..errors import TemporaryBlockchainError, PermanentBlockchainError
from .base import AssetProvider

class MockAssetProvider(AssetProvider):
    """
    Mock asset provider for testing and development.
    This implementation simulates blockchain asset management without actual blockchain interactions.
    """
    
    def __init__(self):
        # In-memory storage for assets
        self._assets = {}
        # Configurable delay to simulate network latency (in seconds)
        self.simulated_delay = 0.5
        # Configurable failure rate (0.0 to 1.0)
        self.failure_rate = 0.0
    
    async def create_asset(self, owner_address: str, metadata: Dict) -> Dict:
        """Create a new asset."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while creating asset for {owner_address}")
        
        # Validate inputs
        if not owner_address:
            raise PermanentBlockchainError("Owner address is required")
        
        if not metadata:
            raise PermanentBlockchainError("Asset metadata is required")
        
        # Create asset ID
        asset_id = f"mock-asset-{uuid.uuid4()}"
        
        # Record asset
        timestamp = datetime.now().isoformat()
        transaction_id = f"mock-tx-{uuid.uuid4()}"
        
        asset = {
            "asset_id": asset_id,
            "owner_address": owner_address,
            "metadata": metadata,
            "created_at": timestamp,
            "updated_at": timestamp,
            "transaction_id": transaction_id
        }
        self._assets[asset_id] = asset
        
        return {
            "asset_id": asset_id,
            "owner_address": owner_address,
            "metadata": metadata,
            "created_at": timestamp,
            "transaction_id": transaction_id
        }
    
    async def transfer_asset(self, asset_id: str, from_address: str, to_address: str) -> Dict:
        """Transfer an asset to a new owner."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while transferring asset {asset_id}")
        
        # Validate inputs
        if not asset_id or not from_address or not to_address:
            raise PermanentBlockchainError("Asset ID, from address, and to address are required")
        
        # Check if asset exists
        if asset_id not in self._assets:
            raise PermanentBlockchainError(f"Asset not found: {asset_id}")
        
        # Check ownership
        asset = self._assets[asset_id]
        if asset["owner_address"] != from_address:
            raise PermanentBlockchainError(f"Asset {asset_id} is not owned by {from_address}")
        
        # Update ownership
        timestamp = datetime.now().isoformat()
        transaction_id = f"mock-tx-{uuid.uuid4()}"
        
        asset["owner_address"] = to_address
        asset["updated_at"] = timestamp
        
        return {
            "success": True,
            "asset_id": asset_id,
            "from_address": from_address,
            "to_address": to_address,
            "transaction_id": transaction_id,
            "timestamp": timestamp
        }
    
    async def get_assets(self, owner_address: str) -> List[Dict]:
        """Get assets owned by an address."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Validate inputs
        if not owner_address:
            raise PermanentBlockchainError("Owner address is required")
        
        # Find assets owned by the address
        owned_assets = []
        for asset in self._assets.values():
            if asset["owner_address"] == owner_address:
                owned_assets.append({
                    "asset_id": asset["asset_id"],
                    "owner_address": asset["owner_address"],
                    "metadata": asset["metadata"],
                    "created_at": asset["created_at"]
                })
        
        return owned_assets
    
    async def update_asset_metadata(self, asset_id: str, metadata: Dict) -> Dict:
        """Update asset metadata."""
        # Simulate network delay
        await self._simulate_delay()
        
        # Simulate random failures
        if self._should_fail():
            raise TemporaryBlockchainError(f"Network error while updating asset {asset_id}")
        
        # Validate inputs
        if not asset_id:
            raise PermanentBlockchainError("Asset ID is required")
        
        if not metadata:
            raise PermanentBlockchainError("Asset metadata is required")
        
        # Check if asset exists
        if asset_id not in self._assets:
            raise PermanentBlockchainError(f"Asset not found: {asset_id}")
        
        # Update metadata
        asset = self._assets[asset_id]
        timestamp = datetime.now().isoformat()
        transaction_id = f"mock-tx-{uuid.uuid4()}"
        
        # Deep merge new metadata with existing
        updated_metadata = self._deep_merge(asset["metadata"], metadata)
        asset["metadata"] = updated_metadata
        asset["updated_at"] = timestamp
        
        return {
            "asset_id": asset_id,
            "owner_address": asset["owner_address"],
            "metadata": updated_metadata,
            "updated_at": timestamp,
            "transaction_id": transaction_id
        }
    
    # Helper methods
    
    def _deep_merge(self, original: Dict, update: Dict) -> Dict:
        """
        Deep merge two dictionaries, recursively merging nested dictionaries.
        
        Args:
            original: The original dictionary
            update: The dictionary with updates to apply
            
        Returns:
            A new dictionary with the merged contents
        """
        result = original.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Replace or add non-dictionary values
                result[key] = value
                
        return result
    
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
    
    def get_all_assets(self) -> List[Dict]:
        """Get all assets for testing purposes."""
        return list(self._assets.values())
    
    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset for testing purposes."""
        if asset_id in self._assets:
            del self._assets[asset_id]
            return True
        return False
