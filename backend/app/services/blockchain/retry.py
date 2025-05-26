import asyncio
from typing import Callable, Any, Dict, Optional
from .errors import BlockchainError, TemporaryBlockchainError

async def retry_async_operation(
    operation: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    **kwargs
) -> Any:
    """
    Retry an async operation with exponential backoff.
    
    Args:
        operation: The async function to retry
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay between retries
        **kwargs: Arguments to pass to the operation
        
    Returns:
        The result of the operation if successful
        
    Raises:
        BlockchainError: If all retry attempts fail
    """
    attempt = 0
    delay = initial_delay
    
    while attempt < max_attempts:
        try:
            return await operation(**kwargs)
        except TemporaryBlockchainError as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            # Log the retry attempt
            print(f"Temporary error: {e.message}. Retrying in {delay} seconds. Attempt {attempt}/{max_attempts}")
            
            await asyncio.sleep(delay)
            delay *= backoff_factor
        except BlockchainError as e:
            if not e.retry_allowed:
                raise
            
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            # Log the retry attempt
            print(f"Blockchain error: {e.message}. Retrying in {delay} seconds. Attempt {attempt}/{max_attempts}")
            
            await asyncio.sleep(delay)
            delay *= backoff_factor
