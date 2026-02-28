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
    _wallet_provider_instance = None
    _payment_provider_instance = None
    _transaction_provider_instance = None
    _asset_provider_instance = None
    
    @staticmethod
    def get_wallet_provider(provider_type: str = "mock") -> WalletProvider:
        providers: Dict[str, Type[WalletProvider]] = {
            "mock": MockWalletProvider,
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported wallet provider type: {provider_type}")
        
        if BlockchainServiceFactory._wallet_provider_instance is None:
            BlockchainServiceFactory._wallet_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._wallet_provider_instance
    
    @staticmethod
    def get_payment_provider(provider_type: str = "mock") -> PaymentProvider:
        providers: Dict[str, Type[PaymentProvider]] = {
            "mock": MockPaymentProvider,
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported payment provider type: {provider_type}")
        
        if BlockchainServiceFactory._payment_provider_instance is None:
            BlockchainServiceFactory._payment_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._payment_provider_instance
    
    @staticmethod
    def get_transaction_provider(provider_type: str = "mock") -> TransactionProvider:
        providers: Dict[str, Type[TransactionProvider]] = {
            "mock": MockTransactionProvider,
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported transaction provider type: {provider_type}")
        
        if BlockchainServiceFactory._transaction_provider_instance is None:
            BlockchainServiceFactory._transaction_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._transaction_provider_instance
    
    @staticmethod
    def get_asset_provider(provider_type: str = "mock") -> AssetProvider:
        providers: Dict[str, Type[AssetProvider]] = {
            "mock": MockAssetProvider,
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unsupported asset provider type: {provider_type}")
        
        if BlockchainServiceFactory._asset_provider_instance is None:
            BlockchainServiceFactory._asset_provider_instance = providers[provider_type]()
            
        return BlockchainServiceFactory._asset_provider_instance
    
    @staticmethod
    def reset_providers() -> None:
        BlockchainServiceFactory._wallet_provider_instance = None
        BlockchainServiceFactory._payment_provider_instance = None
        BlockchainServiceFactory._transaction_provider_instance = None
        BlockchainServiceFactory._asset_provider_instance = None
