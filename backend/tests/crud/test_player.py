from sqlalchemy.orm import Session

from app.crud.player import crud_player
from app.schemas.player import PlayerCreate, PlayerUpdate
from app.models.models import Player


def test_create_player(db_session: Session):
    wallet = "0xaabbccddee1234567890"
    username = "test_create_user"
    player_in = PlayerCreate(wallet_address=wallet, username=username)
    player = crud_player.create(db_session, obj_in=player_in)

    assert player.username == username
    assert player.wallet_address == wallet
    assert player.balance == 0.0
    assert player.wins == 0
    assert player.kills == 0
    assert player.total_earnings == 0.0


def test_create_player_auto_username(db_session: Session):
    wallet = "0xdeadbeef0000"
    player_in = PlayerCreate(wallet_address=wallet)
    player = crud_player.create(db_session, obj_in=player_in)

    assert player.wallet_address == wallet
    assert player.username == f"Player_{wallet[:6]}"


def test_get_player(db_session: Session, test_player: Player):
    player = crud_player.get(db_session, id=test_player.id)
    assert player
    assert player.id == test_player.id
    assert player.username == test_player.username


def test_get_player_by_username(db_session: Session, test_player: Player):
    player = crud_player.get_by_username(db_session, username=test_player.username)
    assert player
    assert player.id == test_player.id


def test_get_player_by_wallet_address(db_session: Session, test_player: Player):
    player = crud_player.get_by_wallet_address(db_session, wallet_address=test_player.wallet_address)
    assert player
    assert player.id == test_player.id


def test_update_player(db_session: Session, test_player: Player):
    new_username = "updated_username"
    player_update = PlayerUpdate(username=new_username)
    updated_player = crud_player.update(db_session, db_obj=test_player, obj_in=player_update)

    assert updated_player.username == new_username
    assert updated_player.id == test_player.id


def test_update_player_balance(db_session: Session, test_player: Player):
    initial_balance = test_player.balance
    amount_to_add = 50.0

    updated_player = crud_player.update_player_balance(db_session, player_id=test_player.id, amount=amount_to_add)

    assert updated_player.balance == initial_balance + amount_to_add


def test_add_win(db_session: Session, test_player: Player):
    initial_wins = test_player.wins
    updated_player = crud_player.add_win(db_session, player_id=test_player.id)
    assert updated_player.wins == initial_wins + 1


def test_add_kill(db_session: Session, test_player: Player):
    initial_kills = test_player.kills
    updated_player = crud_player.add_kill(db_session, player_id=test_player.id)
    assert updated_player.kills == initial_kills + 1
