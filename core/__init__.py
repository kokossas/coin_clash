"""
Coin Clash core module.
This package contains the core functionality for the Coin Clash text-based battle royale game.
"""

# Make sure our new modular structure works with original imports 
# by re-exporting everything from their new locations

# Original models.py imports
from .database.models import *
from .database.models import init_db

# Original db.py imports
from .database.db import get_session

# Original engine.py imports - use the new match/engine.py but expose it at the core level
from .match.engine import MatchEngine as _MatchEngine
class MatchEngine(_MatchEngine):
    pass

# Original repositories.py imports - re-export from their new homes
from .common.repository import BaseRepo
from .player.repository import PlayerRepo, SqlPlayerRepo
from .player.character_repository import CharacterRepo, SqlCharacterRepo
from .player.item_repository import ItemRepo, SqlItemRepo
from .match.repository import MatchRepo, SqlMatchRepo
from .match.event_repository import EventRepo, SqlEventRepo

# Original services.py imports
from .player.service import PlayerService, CharacterService
from .match.service import MatchService

# Original utils.py imports
from .common.utils import SeedableRandom, get_next_character_name

# Original exceptions.py imports
from .common.exceptions import (
    InsufficientParticipantsError, 
    SkipEvent, 
    CriticalMatchError, 
    InsufficientBalanceError,
    MatchAlreadyActiveError,
    SchedulerError
)

# Original config-related imports
from .config.config_loader import load_config
from .match.scenario_loader import load_scenarios, EVENT_TYPE_TO_CATEGORY

# Original scheduler.py
from .scheduler.scheduler import scheduler
