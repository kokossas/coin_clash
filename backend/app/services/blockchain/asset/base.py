from abc import ABC, abstractmethod
from typing import Dict, List

class AssetProvider(ABC):
    """
    Abstract asset provider interface.
    This interface can be implemented by both traditional and blockchain-based asset providers.
    """
    
    @abstractmethod
    async def create_asset(self, owner_address: str, metadata: Dict) -> Dict:
        """
        Create a new asset.
        
        Args:
            owner_address: The blockchain wallet address that will own the asset
            metadata: Dictionary containing asset metadata
            
        Returns:
            Dict containing asset details including:
            - asset_id: Unique identifier for the asset
            - owner_address: The owner's wallet address
            - metadata: The asset metadata
            - created_at: Timestamp when the asset was created
            - transaction_id: ID of the transaction that created the asset (if applicable)
        """
        pass
    
    @abstractmethod
    async def transfer_asset(self, asset_id: str, from_address: str, to_address: str) -> Dict:
        """
        Transfer an asset to a new owner.
        
        Args:
            asset_id: Unique identifier for the asset
            from_address: The current owner's wallet address
            to_address: The new owner's wallet address
            
        Returns:
            Dict containing transfer details including:
            - success: Boolean indicating if the transfer was successful
            - asset_id: Unique identifier for the asset
            - from_address: The previous owner's wallet address
            - to_address: The new owner's wallet address
            - transaction_id: ID of the transfer transaction (if applicable)
            - timestamp: When the transfer occurred
        """
        pass
    
    @abstractmethod
    async def get_assets(self, owner_address: str) -> List[Dict]:
        """
        Get assets owned by an address.
        
        Args:
            owner_address: The blockchain wallet address
            
        Returns:
            List of asset dictionaries, each containing:
            - asset_id: Unique identifier for the asset
            - owner_address: The owner's wallet address
            - metadata: The asset metadata
            - created_at: Timestamp when the asset was created
        """
        pass
    
    @abstractmethod
    async def update_asset_metadata(self, asset_id: str, metadata: Dict) -> Dict:
        """
        Update asset metadata.
        
        Args:
            asset_id: Unique identifier for the asset
            metadata: New metadata to apply (will be merged with existing)
            
        Returns:
            Dict containing updated asset details including:
            - asset_id: Unique identifier for the asset
            - owner_address: The owner's wallet address
            - metadata: The updated asset metadata
            - updated_at: Timestamp when the metadata was updated
            - transaction_id: ID of the update transaction (if applicable)
        """
        pass
