from backend.app.services.blockchain.errors import BlockchainError, TemporaryBlockchainError, PermanentBlockchainError, BlockchainErrorType

def test_blockchain_error_types():
    # Test that error types are correctly defined
    assert BlockchainErrorType.TEMPORARY.value == "temporary"
    assert BlockchainErrorType.PERMANENT.value == "permanent"
    assert BlockchainErrorType.UNKNOWN.value == "unknown"

def test_base_blockchain_error():
    # Test base blockchain error class
    error = BlockchainError("Test error", BlockchainErrorType.TEMPORARY, True)
    
    assert error.message == "Test error"
    assert error.error_type == BlockchainErrorType.TEMPORARY
    assert error.retry_allowed is True
    assert str(error) == "Test error"

def test_temporary_blockchain_error():
    # Test temporary blockchain error class
    error = TemporaryBlockchainError("Network timeout")
    
    assert error.message == "Network timeout"
    assert error.error_type == BlockchainErrorType.TEMPORARY
    assert error.retry_allowed is True

def test_permanent_blockchain_error():
    # Test permanent blockchain error class
    error = PermanentBlockchainError("Invalid address")
    
    assert error.message == "Invalid address"
    assert error.error_type == BlockchainErrorType.PERMANENT
    assert error.retry_allowed is False
