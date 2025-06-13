from typing import Dict, Type
from .wallet.base import WalletProvider
from .payment.base import PaymentProvider
from .transaction.base import TransactionProvider
from .asset.base import AssetProvider

from .wallet.mock_provider import MockWalletProvider
from .payment.mock_provider import MockPaymentProvider
from .transaction.mock_provider import MockTransactionProvider
from .asset.mock_provider import MockAssetProvider

class BlockchainServiceFactory:
    """
    Factory class for creating blockchain service providers.
    This allows for easy switching between different provider implementations.
    """
    
    _wallet_provider_instance = None
    _payment_provider_instance = None
    _transaction_provider_instance = None
    _asset_provider_instance = None
    
    @staticmethod
    def get_wallet_provider(provider_type: str = "mock") -> WalletProvider:
        """
        Get a wallet provider instance.
        
        Args:
            provider_type: The type of provider to create ("mock" for now, 
                          will support "polygon", "solana", etc. in Phase 3)
                          
        Returns:
            An instance of a WalletProvider implementation
            
        Raises:
            ValueError: If the provider type is not supported
        """
        providers: Dict[str, Type[WalletProvider]] = {
            "mock": MockWalletProvider,
            # Add real providers in Phase 3
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported wallet provider type: {provider_type}")
        
        # Use singleton pattern for providers
        if BlockchainServiceFactory._wallet_provider_instance is None:
            BlockchainServiceFactory._wallet_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._wallet_provider_instance
    
    @staticmethod
    def get_payment_provider(provider_type: str = "mock") -> PaymentProvider:
        """
        Get a payment provider instance.
        
        Args:
            provider_type: The type of provider to create ("mock" for now, 
                          will support "polygon", "solana", etc. in Phase 3)
                          
        Returns:
            An instance of a PaymentProvider implementation
            
        Raises:
            ValueError: If the provider type is not supported
        """
        providers: Dict[str, Type[PaymentProvider]] = {
            "mock": MockPaymentProvider,
            # Add real providers in Phase 3
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported payment provider type: {provider_type}")
        
        # Use singleton pattern for providers
        if BlockchainServiceFactory._payment_provider_instance is None:
            BlockchainServiceFactory._payment_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._payment_provider_instance
    
    @staticmethod
    def get_transaction_provider(provider_type: str = "mock") -> TransactionProvider:
        """
        Get a transaction provider instance.
        
        Args:
            provider_type: The type of provider to create ("mock" for now, 
                          will support "polygon", "solana", etc. in Phase 3)
                          
        Returns:
            An instance of a TransactionProvider implementation
            
        Raises:
            ValueError: If the provider type is not supported
        """
        providers: Dict[str, Type[TransactionProvider]] = {
            "mock": MockTransactionProvider,
            # Add real providers in Phase 3
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported transaction provider type: {provider_type}")
        
        # Use singleton pattern for providers
        if BlockchainServiceFactory._transaction_provider_instance is None:
            BlockchainServiceFactory._transaction_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._transaction_provider_instance
    
    @staticmethod
    def get_asset_provider(provider_type: str = "mock") -> AssetProvider:
        """
        Get an asset provider instance.
        
        Args:
            provider_type: The type of provider to create ("mock" for now, 
                          will support "polygon", "solana", etc. in Phase 3)
                          
        Returns:
            An instance of an AssetProvider implementation
            
        Raises:
            ValueError: If the provider type is not supported
        """
        providers: Dict[str, Type[AssetProvider]] = {
            "mock": MockAssetProvider,
            # Add real providers in Phase 3
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported asset provider type: {provider_type}")
        
        # Use singleton pattern for providers
        if BlockchainServiceFactory._asset_provider_instance is None:
            BlockchainServiceFactory._asset_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._asset_provider_instance
    
    @staticmethod
    def reset_providers() -> None:
        """
        Reset all provider instances.
        Useful for testing to ensure a clean state.
        """
        BlockchainServiceFactory._wallet_provider_instance = None
        BlockchainServiceFactory._payment_provider_instance = None
        BlockchainServiceFactory._transaction_provider_instance = None
        BlockchainServiceFactory._asset_provider_instance = None
