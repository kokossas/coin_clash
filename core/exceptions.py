class InsufficientParticipantsError(Exception):
    """Raised when a scenario template expects more characters than are available."""
    pass

class SkipEvent(Exception):
    """Non-fatal. Skip the current event and continue the match."""
    pass

class CriticalMatchError(Exception):
    """Fatal. Abort the match and surface a 500 to the API/UI."""
    pass