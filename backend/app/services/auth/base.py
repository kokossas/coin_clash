from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class AuthProvider(ABC):

    @abstractmethod
    async def create_challenge(self, wallet_address: str) -> str:
        """Return a nonce the client must sign to prove wallet ownership."""
        pass

    @abstractmethod
    async def verify_challenge(
        self, wallet_address: str, signature: str, nonce: str,
    ) -> bool:
        """Verify signed nonce. Return True if signature is valid."""
        pass

    @abstractmethod
    async def generate_token(
        self, wallet_address: str, player_id: int,
    ) -> str:
        """Generate a JWT containing wallet_address and player_id."""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT. Return payload dict with wallet_address and player_id, or None."""
        pass
