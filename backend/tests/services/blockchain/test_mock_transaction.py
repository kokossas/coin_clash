import asyncio
import pytest
from backend.app.services.blockchain.transaction.mock_provider import MockTransactionProvider
from backend.app.services.blockchain.errors import TemporaryBlockchainError, PermanentBlockchainError

@pytest.fixture
def transaction_provider():
    provider = MockTransactionProvider()
    # Set delay to 0 for faster tests
    provider.simulated_delay = 0
    # Set confirmation time to 0 for faster tests
    provider.confirmation_time = 0.1
    return provider

@pytest.mark.asyncio
async def test_create_transaction_success(transaction_provider):
    # Test successful transaction creation
    from_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    amount = 100.0
    currency = "MATIC"
    
    result = await transaction_provider.create_transaction(from_address, to_address, amount, currency)
    
    assert "transaction_id" in result
    assert result["status"] == "pending"
    assert result["from_address"] == from_address
    assert result["to_address"] == to_address
    assert result["amount"] == amount
    assert result["currency"] == currency
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_create_transaction_invalid_amount(transaction_provider):
    # Test transaction with invalid amount
    from_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    amount = -10.0  # Negative amount
    currency = "MATIC"
    
    with pytest.raises(PermanentBlockchainError):
        await transaction_provider.create_transaction(from_address, to_address, amount, currency)

@pytest.mark.asyncio
async def test_create_transaction_network_error(transaction_provider):
    # Test transaction with network error
    from_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    amount = 100.0
    currency = "MATIC"
    
    # Set failure rate to 100% to simulate network error
    transaction_provider.failure_rate = 1.0
    
    with pytest.raises(TemporaryBlockchainError):
        await transaction_provider.create_transaction(from_address, to_address, amount, currency)
    
    # Reset failure rate for other tests
    transaction_provider.failure_rate = 0.0

@pytest.mark.asyncio
async def test_get_transaction_status(transaction_provider):
    # First create a transaction
    from_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    amount = 100.0
    currency = "MATIC"
    
    tx_result = await transaction_provider.create_transaction(from_address, to_address, amount, currency)
    transaction_id = tx_result["transaction_id"]
    
    # Wait a moment for the transaction to be processed
    await asyncio.sleep(0.2)
    
    # Then get its status
    status_result = await transaction_provider.get_transaction_status(transaction_id)
    
    assert status_result["transaction_id"] == transaction_id
    assert status_result["status"] in ["pending", "confirmed", "failed"]
    assert "confirmations" in status_result
    assert "timestamp" in status_result

@pytest.mark.asyncio
async def test_get_transaction_status_nonexistent(transaction_provider):
    # Test getting status of a nonexistent transaction
    transaction_id = "nonexistent-tx-id"
    
    with pytest.raises(PermanentBlockchainError):
        await transaction_provider.get_transaction_status(transaction_id)

@pytest.mark.asyncio
async def test_get_transaction_history(transaction_provider):
    # Create multiple transactions for a wallet
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    
    # Create 3 transactions
    for i in range(3):
        await transaction_provider.create_transaction(
            wallet_address, 
            to_address, 
            100.0 * (i + 1), 
            "MATIC"
        )
    
    # Get transaction history
    history = await transaction_provider.get_transaction_history(wallet_address, limit=10)
    
    assert len(history) == 3
    for tx in history:
        assert "transaction_id" in tx
        assert "status" in tx
        assert "from_address" in tx
        assert "to_address" in tx
        assert "amount" in tx
        assert "currency" in tx
        assert "timestamp" in tx

@pytest.mark.asyncio
async def test_get_transaction_history_limit(transaction_provider):
    # Create multiple transactions for a wallet
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    
    # Create 5 transactions
    for i in range(5):
        await transaction_provider.create_transaction(
            wallet_address, 
            to_address, 
            100.0 * (i + 1), 
            "MATIC"
        )
    
    # Get transaction history with limit
    history = await transaction_provider.get_transaction_history(wallet_address, limit=2)
    
    assert len(history) == 2

@pytest.mark.asyncio
async def test_retry_transaction(transaction_provider):
    # First create a transaction
    from_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    amount = 100.0
    currency = "MATIC"
    
    tx_result = await transaction_provider.create_transaction(from_address, to_address, amount, currency)
    transaction_id = tx_result["transaction_id"]
    
    # Manually set the transaction to failed
    transaction_provider.set_transaction_status(transaction_id, "failed")
    
    # Retry the transaction
    retry_result = await transaction_provider.retry_transaction(transaction_id)
    
    assert "transaction_id" in retry_result
    assert retry_result["transaction_id"] != transaction_id  # Should be a new ID
    assert retry_result["status"] == "pending"
    assert "original_transaction_id" in retry_result
    assert retry_result["original_transaction_id"] == transaction_id
    assert "timestamp" in retry_result

@pytest.mark.asyncio
async def test_retry_transaction_not_failed(transaction_provider):
    # First create a transaction
    from_address = "0x1234567890abcdef1234567890abcdef12345678"
    to_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    amount = 100.0
    currency = "MATIC"
    
    tx_result = await transaction_provider.create_transaction(from_address, to_address, amount, currency)
    transaction_id = tx_result["transaction_id"]
    
    # Manually set the transaction to confirmed
    transaction_provider.set_transaction_status(transaction_id, "confirmed")
    
    # Try to retry a confirmed transaction
    with pytest.raises(PermanentBlockchainError):
        await transaction_provider.retry_transaction(transaction_id)
