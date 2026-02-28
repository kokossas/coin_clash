import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any

from jose import jwt

from .base import AuthProvider
from ...core.config import settings
from ..blockchain.factory import BlockchainServiceFactory


class JWTAuthProvider(AuthProvider):

    def __init__(self) -> None:
        self._pending_nonces: Dict[str, str] = {}

    async def create_challenge(self, wallet_address: str) -> str:
        nonce = secrets.token_hex(32)
        self._pending_nonces[wallet_address.lower()] = nonce
        return nonce

    async def verify_challenge(
        self, wallet_address: str, signature: str, nonce: str,
    ) -> bool:
        addr = wallet_address.lower()
        stored_nonce = self._pending_nonces.pop(addr, None)
        if stored_nonce is None or stored_nonce != nonce:
            return False

        wallet_provider = BlockchainServiceFactory.get_wallet_provider()
        return await wallet_provider.verify_signature(addr, nonce, signature)

    async def generate_token(
        self, wallet_address: str, player_id: int,
    ) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        to_encode = {
            "sub": wallet_address,
            "player_id": player_id,
            "exp": expire,
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            wallet_address = payload.get("sub")
            player_id = payload.get("player_id")
            if wallet_address is None or player_id is None:
                return None
            return {"wallet_address": wallet_address, "player_id": player_id}
        except Exception:
            return None
