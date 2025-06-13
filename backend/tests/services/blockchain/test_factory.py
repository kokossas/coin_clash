import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.blockchain.factory import BlockchainServiceFactory
from backend.app.services.blockchain.wallet.mock_provider import MockWalletProvider
from backend.app.services.blockchain.payment.mock_provider import MockPaymentProvider
from backend.app.services.blockchain.transaction.mock_provider import MockTransactionProvider
from backend.app.services.blockchain.asset.mock_provider import MockAssetProvider

@pytest.fixture(autouse=True)
def reset_factory():
    """Reset the factory before each test to ensure a clean state."""
    BlockchainServiceFactory.reset_providers()
    yield

def test_get_wallet_provider():
    # Test getting a wallet provider
    provider = BlockchainServiceFactory.get_wallet_provider("mock")
    
    assert provider is not None
    assert isinstance(provider, MockWalletProvider)
    
    # Test singleton pattern
    provider2 = BlockchainServiceFactory.get_wallet_provider("mock")
    assert provider is provider2  # Should be the same instance

def test_get_payment_provider():
    # Test getting a payment provider
    provider = BlockchainServiceFactory.get_payment_provider("mock")
    
    assert provider is not None
    assert isinstance(provider, MockPaymentProvider)
    
    # Test singleton pattern
    provider2 = BlockchainServiceFactory.get_payment_provider("mock")
    assert provider is provider2  # Should be the same instance

def test_get_transaction_provider():
    # Test getting a transaction provider
    provider = BlockchainServiceFactory.get_transaction_provider("mock")
    
    assert provider is not None
    assert isinstance(provider, MockTransactionProvider)
    
    # Test singleton pattern
    provider2 = BlockchainServiceFactory.get_transaction_provider("mock")
    assert provider is provider2  # Should be the same instance

def test_get_asset_provider():
    # Test getting an asset provider
    provider = BlockchainServiceFactory.get_asset_provider("mock")
    
    assert provider is not None
    assert isinstance(provider, MockAssetProvider)
    
    # Test singleton pattern
    provider2 = BlockchainServiceFactory.get_asset_provider("mock")
    assert provider is provider2  # Should be the same instance

def test_invalid_provider_type():
    # Test getting an invalid provider type
    with pytest.raises(ValueError):
        BlockchainServiceFactory.get_wallet_provider("invalid")
    
    with pytest.raises(ValueError):
        BlockchainServiceFactory.get_payment_provider("invalid")
    
    with pytest.raises(ValueError):
        BlockchainServiceFactory.get_transaction_provider("invalid")
    
    with pytest.raises(ValueError):
        BlockchainServiceFactory.get_asset_provider("invalid")

def test_reset_providers():
    # Get providers
    wallet_provider = BlockchainServiceFactory.get_wallet_provider("mock")
    payment_provider = BlockchainServiceFactory.get_payment_provider("mock")
    transaction_provider = BlockchainServiceFactory.get_transaction_provider("mock")
    asset_provider = BlockchainServiceFactory.get_asset_provider("mock")
    
    # Reset providers
    BlockchainServiceFactory.reset_providers()
    
    # Get new providers
    new_wallet_provider = BlockchainServiceFactory.get_wallet_provider("mock")
    new_payment_provider = BlockchainServiceFactory.get_payment_provider("mock")
    new_transaction_provider = BlockchainServiceFactory.get_transaction_provider("mock")
    new_asset_provider = BlockchainServiceFactory.get_asset_provider("mock")
    
    # Should be different instances
    assert wallet_provider is not new_wallet_provider
    assert payment_provider is not new_payment_provider
    assert transaction_provider is not new_transaction_provider
    assert asset_provider is not new_asset_provider
