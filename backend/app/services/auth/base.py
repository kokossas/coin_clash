from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

class AuthProvider(ABC):
    """
    Abstract authentication provider interface.
    This interface can be implemented by both traditional and wallet-based authentication providers.
    """
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate a user with the provided credentials."""
        pass
    
    @abstractmethod
    async def generate_token(self, user_id: int) -> str:
        """Generate an authentication token for the user."""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify an authentication token and return the user information."""
        pass
