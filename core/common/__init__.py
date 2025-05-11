"""Common utilities and shared functionality for Coin Clash.

This package contains utility functions, base classes, and exception definitions
that are used across multiple modules in the project.
"""

from .utils import SeedableRandom, get_next_character_name
from .repository import BaseRepo
from .exceptions import (
    InsufficientParticipantsError,
    SkipEvent,
    CriticalMatchError,
    InsufficientBalanceError,
    MatchAlreadyActiveError,
    SchedulerError
)
