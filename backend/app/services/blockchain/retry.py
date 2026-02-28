import asyncio
from typing import Callable, Any
from .errors import BlockchainError, TemporaryBlockchainError

async def retry_async_operation(
    operation: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    **kwargs
) -> Any:
    attempt = 0
    delay = initial_delay
    
    while attempt < max_attempts:
        try:
            return await operation(**kwargs)
        except TemporaryBlockchainError as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            print(f"Temporary error: {e.message}. Retrying in {delay} seconds. Attempt {attempt}/{max_attempts}")
            
            await asyncio.sleep(delay)
            delay *= backoff_factor
        except BlockchainError as e:
            if not e.retry_allowed:
                raise
            
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            print(f"Blockchain error: {e.message}. Retrying in {delay} seconds. Attempt {attempt}/{max_attempts}")
            
            await asyncio.sleep(delay)
            delay *= backoff_factor
