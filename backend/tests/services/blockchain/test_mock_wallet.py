import pytest
from backend.app.services.blockchain.wallet.mock_provider import MockWalletProvider
from backend.app.services.blockchain.errors import TemporaryBlockchainError, PermanentBlockchainError

@pytest.fixture
def wallet_provider():
    provider = MockWalletProvider()
    # Set delay to 0 for faster tests
    provider.simulated_delay = 0
    return provider

@pytest.mark.asyncio
async def test_connect_wallet_success(wallet_provider):
    # Test successful wallet connection
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    chain_id = "polygon-1"
    
    result = await wallet_provider.connect_wallet(wallet_address, chain_id)
    
    assert result["success"] is True
    assert result["wallet_address"] == wallet_address
    assert result["chain_id"] == chain_id
    assert "connection_id" in result

@pytest.mark.asyncio
async def test_connect_wallet_invalid_chain(wallet_provider):
    # Test connection with invalid chain ID
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    invalid_chain_id = "invalid-chain"
    
    with pytest.raises(PermanentBlockchainError):
        await wallet_provider.connect_wallet(wallet_address, invalid_chain_id)

@pytest.mark.asyncio
async def test_connect_wallet_network_error(wallet_provider):
    # Test connection with network error
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    chain_id = "polygon-1"
    
    # Set failure rate to 100% to simulate network error
    wallet_provider.failure_rate = 1.0
    
    with pytest.raises(TemporaryBlockchainError):
        await wallet_provider.connect_wallet(wallet_address, chain_id)
    
    # Reset failure rate for other tests
    wallet_provider.failure_rate = 0.0

@pytest.mark.asyncio
async def test_disconnect_wallet(wallet_provider):
    # First connect a wallet
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    chain_id = "polygon-1"
    await wallet_provider.connect_wallet(wallet_address, chain_id)
    
    # Then disconnect it
    result = await wallet_provider.disconnect_wallet(wallet_address)
    
    assert result["success"] is True
    assert result["wallet_address"] == wallet_address

@pytest.mark.asyncio
async def test_disconnect_wallet_not_connected(wallet_provider):
    # Test disconnecting a wallet that isn't connected
    wallet_address = "0xnonexistentwallet"
    
    result = await wallet_provider.disconnect_wallet(wallet_address)
    
    assert result["success"] is False
    assert result["wallet_address"] == wallet_address
    assert "error" in result

@pytest.mark.asyncio
async def test_verify_signature_valid(wallet_provider):
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    message = "Test message"
    signature = "0x1234567890abcdef" # Mock valid signature format
    
    result = await wallet_provider.verify_signature(wallet_address, message, signature)
    
    assert result is True

@pytest.mark.asyncio
async def test_verify_signature_invalid(wallet_provider):
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    message = "Test message"
    signature = "invalid" # Invalid signature format
    
    result = await wallet_provider.verify_signature(wallet_address, message, signature)
    
    assert result is False

@pytest.mark.asyncio
async def test_get_supported_chains(wallet_provider):
    chains = await wallet_provider.get_supported_chains()
    
    assert len(chains) > 0
    assert "chain_id" in chains[0]
    assert "name" in chains[0]
    assert "currency" in chains[0]
    assert "is_testnet" in chains[0]

@pytest.mark.asyncio
async def test_add_supported_chain(wallet_provider):
    # Add a new chain
    chain_id = "test-chain-123"
    name = "Test Chain"
    currency = "TEST"
    is_testnet = True
    
    wallet_provider.add_supported_chain(chain_id, name, currency, is_testnet)
    
    # Get chains and verify the new one is included
    chains = await wallet_provider.get_supported_chains()
    
    found = False
    for chain in chains:
        if chain["chain_id"] == chain_id:
            found = True
            assert chain["name"] == name
            assert chain["currency"] == currency
            assert chain["is_testnet"] == is_testnet
            break
    
    assert found, "Added chain not found in supported chains"
