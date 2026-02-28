import pytest
import asyncio
from backend.app.services.blockchain.errors import TemporaryBlockchainError, PermanentBlockchainError
from backend.app.services.blockchain.retry import retry_async_operation

@pytest.mark.asyncio
async def test_retry_successful_operation():
    # Test a successful operation that doesn't need retries
    async def successful_operation():
        return "success"
    
    result = await retry_async_operation(successful_operation)
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_temporary_error():
    # Test an operation that fails with a temporary error but succeeds on retry
    attempt_count = 0
    
    async def failing_then_succeeding_operation():
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count == 1:
            # Fail on first attempt
            raise TemporaryBlockchainError("Temporary network error")
        else:
            # Succeed on subsequent attempts
            return "success after retry"
    
    result = await retry_async_operation(
        failing_then_succeeding_operation,
        max_attempts=3,
        initial_delay=0.1,
        backoff_factor=1.0
    )
    
    assert result == "success after retry"
    assert attempt_count == 2  # Should have succeeded on the second attempt

@pytest.mark.asyncio
async def test_retry_permanent_error():
    # Test an operation that fails with a permanent error
    async def permanently_failing_operation():
        raise PermanentBlockchainError("Insufficient funds")
    
    with pytest.raises(PermanentBlockchainError):
        await retry_async_operation(permanently_failing_operation)

@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded():
    # Test an operation that keeps failing until max attempts are exceeded
    attempt_count = 0
    
    async def always_failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        raise TemporaryBlockchainError(f"Network error, attempt {attempt_count}")
    
    with pytest.raises(TemporaryBlockchainError):
        await retry_async_operation(
            always_failing_operation,
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=1.0
        )
    
    assert attempt_count == 3  # Should have attempted exactly 3 times

@pytest.mark.asyncio
async def test_retry_with_exponential_backoff():
    # Test that exponential backoff is working correctly
    attempt_count = 0
    start_times = []
    
    async def always_failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        start_times.append(asyncio.get_event_loop().time())
        raise TemporaryBlockchainError(f"Network error, attempt {attempt_count}")
    
    try:
        await retry_async_operation(
            always_failing_operation,
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=2.0
        )
    except TemporaryBlockchainError:
        pass
    
    assert attempt_count == 3
    
    # Check that delays between attempts follow exponential backoff
    if len(start_times) >= 3:
        first_delay = start_times[1] - start_times[0]
        second_delay = start_times[2] - start_times[1]
        
        # Second delay should be approximately twice the first delay
        # Allow some margin for timing variations
        assert second_delay > first_delay * 1.5
