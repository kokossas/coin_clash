import logging
from typing import List

from sqlalchemy.orm import Session

from backend.app.crud.pending_payout import crud_pending_payout
from backend.app.crud.player import crud_player
from backend.app.models.models import PendingPayout
from backend.app.services.blockchain.factory import BlockchainServiceFactory

logger = logging.getLogger(__name__)


class SettlementService:

    def __init__(self) -> None:
        self._payment = BlockchainServiceFactory.get_payment_provider()

    async def settle_match(self, db: Session, match_id: int) -> List[PendingPayout]:
        unsettled = [
            p for p in crud_pending_payout.get_by_match_id(db, match_id)
            if p.settled_at is None
        ]
        settled: List[PendingPayout] = []
        for payout in unsettled:
            result = await self._settle_payout(db, payout)
            if result is not None:
                settled.append(result)
        return settled

    async def _settle_payout(
        self, db: Session, payout: PendingPayout
    ) -> PendingPayout | None:
        player = crud_player.get(db, payout.player_id)
        if player is None:
            logger.error("Player %d not found for payout %d", payout.player_id, payout.id)
            return None

        try:
            result = await self._payment.process_withdrawal(
                wallet_address=player.wallet_address,
                amount=float(payout.amount),
                currency=payout.currency,
            )
        except Exception:
            logger.exception("Settlement failed for payout %d", payout.id)
            return None

        tx_hash = result.get("transaction_id", "")
        return crud_pending_payout.mark_settled(db, payout_id=payout.id, tx_hash=tx_hash)
