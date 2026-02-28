class InsufficientParticipantsError(Exception):
    """Raised when a scenario template expects more characters than are available."""
    pass

class SkipEvent(Exception):
    """Non-fatal. Skip the current event and continue the match."""
    pass

class CriticalMatchError(Exception):
    """Fatal. Abort the match and surface a 500 to the API/UI."""
    pass

class InsufficientBalanceError(Exception):
    """Raised when a player doesn't have enough balance for an operation."""
    pass

class MatchAlreadyActiveError(Exception):
    """Raised when attempting to join or modify a match that has already started."""
    pass

class SchedulerError(Exception):
    """Raised when there's an issue with scheduling or executing background tasks."""
    pass