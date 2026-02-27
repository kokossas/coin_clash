from typing import List

from sqlalchemy.orm import Session

from backend.app.crud.owned_character import crud_owned_character
from backend.app.crud.player import crud_player
from backend.app.models.models import Character, OwnedCharacter
from backend.app.schemas.owned_character import OwnedCharacterCreate
from backend.app.services.blockchain.factory import BlockchainServiceFactory
from core.config.config_loader import load_config
from core.common.utils import get_next_character_name


class CharacterInventoryService:

    def __init__(self) -> None:
        self._config = load_config()
        self._payment = BlockchainServiceFactory.get_payment_provider()

    async def purchase_characters(
        self,
        db: Session,
        player_id: int,
        quantity: int,
        payment_ref: str,
    ) -> List[OwnedCharacter]:
        if quantity < 1 or quantity > 10:
            raise ValueError("quantity must be between 1 and 10")

        player = crud_player.get(db, player_id)
        if player is None:
            raise ValueError(f"Player {player_id} not found")

        total_cost = quantity * self._config["character_base_price"]

        await self._payment.process_deposit(
            wallet_address=payment_ref,
            amount=total_cost,
            currency="USDC",
        )

        created: List[OwnedCharacter] = []
        for _ in range(quantity):
            name = get_next_character_name()
            obj = crud_owned_character.create(
                db, obj_in=OwnedCharacterCreate(player_id=player_id, character_name=name)
            )
            created.append(obj)

        return created

    def get_player_inventory(
        self,
        db: Session,
        player_id: int,
        alive_only: bool = False,
    ) -> List[OwnedCharacter]:
        return crud_owned_character.get_by_player_id(db, player_id, alive_only=alive_only)

    async def revive_character(
        self,
        db: Session,
        character_id: int,
        player_id: int,
        payment_ref: str,
    ) -> OwnedCharacter:
        owned = crud_owned_character.get(db, character_id)
        if owned is None:
            raise ValueError(f"OwnedCharacter {character_id} not found")
        if owned.player_id != player_id:
            raise ValueError("Character not owned by this player")
        if owned.is_alive:
            raise ValueError("Character is already alive")

        # Reject if character is currently in an active match
        in_active_match = (
            db.query(Character)
            .filter(
                Character.owned_character_id == character_id,
                Character.match.has(status="active"),
            )
            .first()
        )
        if in_active_match is not None:
            raise ValueError("Character is in an active match")

        revival_fee = self._config["character_revival_fee"]
        await self._payment.process_deposit(
            wallet_address=payment_ref,
            amount=revival_fee,
            currency="USDC",
        )

        result = crud_owned_character.set_alive(db, character_id=character_id, is_alive=True)
        if result is None:
            raise ValueError("Failed to revive character")
        return result
