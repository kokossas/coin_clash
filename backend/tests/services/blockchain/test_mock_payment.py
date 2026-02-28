import pytest
from backend.app.services.blockchain.payment.mock_provider import MockPaymentProvider
from backend.app.services.blockchain.errors import TemporaryBlockchainError, PermanentBlockchainError

@pytest.fixture
def payment_provider():
    provider = MockPaymentProvider()
    # Set delay to 0 for faster tests
    provider.simulated_delay = 0
    return provider

@pytest.mark.asyncio
async def test_process_deposit_success(payment_provider):
    # Test successful deposit
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    amount = 100.0
    currency = "MATIC"
    
    result = await payment_provider.process_deposit(wallet_address, amount, currency)
    
    assert result["success"] is True
    assert result["amount"] == amount
    assert result["currency"] == currency
    assert "transaction_id" in result
    assert "status" in result
    assert "timestamp" in result
    
    # Verify balance was updated
    balance = await payment_provider.get_balance(wallet_address, currency)
    assert balance == amount

@pytest.mark.asyncio
async def test_process_deposit_invalid_amount(payment_provider):
    # Test deposit with invalid amount
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    amount = -10.0  # Negative amount
    currency = "MATIC"
    
    with pytest.raises(PermanentBlockchainError):
        await payment_provider.process_deposit(wallet_address, amount, currency)

@pytest.mark.asyncio
async def test_process_deposit_network_error(payment_provider):
    # Test deposit with network error
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    amount = 100.0
    currency = "MATIC"
    
    # Set failure rate to 100% to simulate network error
    payment_provider.failure_rate = 1.0
    
    with pytest.raises(TemporaryBlockchainError):
        await payment_provider.process_deposit(wallet_address, amount, currency)
    
    # Reset failure rate for other tests
    payment_provider.failure_rate = 0.0

@pytest.mark.asyncio
async def test_process_withdrawal_success(payment_provider):
    # First deposit some funds
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    deposit_amount = 200.0
    withdrawal_amount = 50.0
    currency = "MATIC"
    
    await payment_provider.process_deposit(wallet_address, deposit_amount, currency)
    
    # Then withdraw a portion
    result = await payment_provider.process_withdrawal(wallet_address, withdrawal_amount, currency)
    
    assert result["success"] is True
    assert result["amount"] == withdrawal_amount
    assert result["currency"] == currency
    assert "transaction_id" in result
    assert "status" in result
    assert "timestamp" in result
    
    # Verify balance was updated
    balance = await payment_provider.get_balance(wallet_address, currency)
    assert balance == deposit_amount - withdrawal_amount

@pytest.mark.asyncio
async def test_process_withdrawal_insufficient_funds(payment_provider):
    # Test withdrawal with insufficient funds
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    amount = 1000.0  # More than available
    currency = "MATIC"
    
    # Set initial balance
    payment_provider.set_balance(wallet_address, currency, 100.0)
    
    with pytest.raises(PermanentBlockchainError):
        await payment_provider.process_withdrawal(wallet_address, amount, currency)

@pytest.mark.asyncio
async def test_get_balance_new_wallet(payment_provider):
    # Test getting balance for a new wallet
    wallet_address = "0xnewwallet"
    currency = "MATIC"
    
    balance = await payment_provider.get_balance(wallet_address, currency)
    
    # New wallets should start with zero balance
    assert balance == 0.0

@pytest.mark.asyncio
async def test_estimate_fees(payment_provider):
    # Test fee estimation
    amount = 100.0
    currency = "MATIC"
    
    result = await payment_provider.estimate_fees(amount, currency)
    
    assert "fee_amount" in result
    assert "fee_currency" in result
    assert "gas_price" in result
    assert "gas_limit" in result
    assert result["fee_currency"] == currency
    
    # Verify fee calculation (0.1% in the mock implementation)
    assert result["fee_amount"] == amount * 0.001

@pytest.mark.asyncio
async def test_set_balance(payment_provider):
    # Test setting a specific balance
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    currency = "MATIC"
    amount = 500.0
    
    payment_provider.set_balance(wallet_address, currency, amount)
    
    balance = await payment_provider.get_balance(wallet_address, currency)
    assert balance == amount

@pytest.mark.asyncio
async def test_multiple_currencies(payment_provider):
    # Test handling multiple currencies for the same wallet
    wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
    
    # Deposit different currencies
    await payment_provider.process_deposit(wallet_address, 100.0, "MATIC")
    await payment_provider.process_deposit(wallet_address, 50.0, "SOL")
    
    # Check balances
    matic_balance = await payment_provider.get_balance(wallet_address, "MATIC")
    sol_balance = await payment_provider.get_balance(wallet_address, "SOL")
    
    assert matic_balance == 100.0
    assert sol_balance == 50.0
