from sqlalchemy.orm import Session

from app.crud.character import crud_character
from app.schemas.character import CharacterCreate
from app.models.models import Character


def test_create_character(db_session: Session, test_player):
    character_in = CharacterCreate(name="Test Character", player_id=test_player.id)
    character = crud_character.create(db_session, obj_in=character_in)

    assert character.name == "Test Character"
    assert character.player_id == test_player.id
    assert character.is_alive is True
    assert character.match_id is None


def test_get_character(db_session: Session, test_character: Character):
    character = crud_character.get(db_session, id=test_character.id)
    assert character
    assert character.id == test_character.id
    assert character.name == test_character.name
    assert character.player_id == test_character.player_id


def test_get_by_player_id(db_session: Session, test_character: Character):
    characters = crud_character.get_by_player_id(db_session, player_id=test_character.player_id)
    assert len(characters) > 0
    assert test_character.id in [c.id for c in characters]


def test_assign_to_match(db_session: Session, test_character: Character, test_match):
    updated_character = crud_character.assign_to_match(
        db_session, character_id=test_character.id, match_id=test_match.id
    )
    assert updated_character.match_id == test_match.id


def test_set_alive_status(db_session: Session, test_character: Character):
    updated_character = crud_character.set_alive_status(
        db_session, character_id=test_character.id, is_alive=False
    )
    assert updated_character.is_alive is False

    updated_character = crud_character.set_alive_status(
        db_session, character_id=test_character.id, is_alive=True
    )
    assert updated_character.is_alive is True
