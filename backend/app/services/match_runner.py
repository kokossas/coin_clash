"""
Entry point for running a match in the background.
Instantiates all core/ repos and drives MatchEngine.
"""

import logging
from sqlalchemy.orm import Session

from core.config.config_loader import load_config
from core.match.scenario_loader import load_scenarios
from core.match.engine import MatchEngine
from core.player.repository import SqlPlayerRepo
from core.player.character_repository import SqlCharacterRepo
from core.player.item_repository import SqlItemRepo
from core.match.repository import SqlMatchRepo
from core.match.event_repository import SqlEventRepo
from backend.app.models.models import Character

logger = logging.getLogger(__name__)


def run_match_background(match_id: int, db: Session) -> None:
    """
    Loads config and scenarios, wires all repos, then runs the match engine.
    Intended as the target for BackgroundTasks and the scheduler.
    """
    config = load_config()
    scenarios = load_scenarios(config["scenario_dir"])

    player_repo = SqlPlayerRepo(db)
    character_repo = SqlCharacterRepo(db)
    item_repo = SqlItemRepo(db)
    match_repo = SqlMatchRepo(db)
    event_repo = SqlEventRepo(db)

    participants = db.query(Character).filter(Character.match_id == match_id).all()

    engine = MatchEngine(
        match_id=match_id,
        config=config,
        scenarios=scenarios,
        player_repo=player_repo,
        character_repo=character_repo,
        match_repo=match_repo,
        event_repo=event_repo,
        item_repo=item_repo,
    )

    engine.run_match(participants)
