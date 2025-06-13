from enum import Enum

class BlockchainErrorType(Enum):
    """
    Enum defining types of blockchain errors for proper handling and recovery.
    """
    TEMPORARY = "temporary"  # Network issues, timeouts
    PERMANENT = "permanent"  # Invalid addresses, insufficient funds
    UNKNOWN = "unknown"      # Unexpected errors

class BlockchainError(Exception):
    """
    Base exception class for blockchain-related errors.
    
    Attributes:
        message: Human-readable error description
        error_type: Type of error (temporary, permanent, unknown)
        retry_allowed: Whether retry attempts are allowed for this error
    """
    def __init__(self, message: str, error_type: BlockchainErrorType, retry_allowed: bool = True):
        self.message = message
        self.error_type = error_type
        self.retry_allowed = retry_allowed
        super().__init__(self.message)

class TemporaryBlockchainError(BlockchainError):
    """
    Exception for temporary blockchain errors that can be retried.
    Examples: network timeouts, congestion, temporary service unavailability.
    """
    def __init__(self, message: str):
        super().__init__(message, BlockchainErrorType.TEMPORARY, True)

class PermanentBlockchainError(BlockchainError):
    """
    Exception for permanent blockchain errors that cannot be retried.
    Examples: invalid addresses, insufficient funds, rejected transactions.
    """
    def __init__(self, message: str):
        super().__init__(message, BlockchainErrorType.PERMANENT, False)

class UnknownBlockchainError(BlockchainError):
    """
    Exception for unexpected blockchain errors with unknown retry status.
    These are typically handled with caution and limited retry attempts.
    """
    def __init__(self, message: str):
        super().__init__(message, BlockchainErrorType.UNKNOWN, True)
