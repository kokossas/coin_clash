from typing import Any, Dict

from pydantic import BaseModel


class ExtraEvents(BaseModel):
    non_lethal_story_chance: float
    extra_lethal_base_chance: float
    comeback_base_chance: float


class LethalModifiers(BaseModel):
    cap_8_plus: float
    cap_12_plus: float


class GameConfig(BaseModel):
    scenario_dir: str

    min_fee: float
    default_fee: float
    max_fee: float

    kill_award_rate_min: float
    kill_award_rate_default: float
    kill_award_rate_max: float

    num_players_min: int
    num_players_default: int
    num_players_max: int

    chars_per_player_min: int
    chars_per_player_max: int

    primary_event_weights: Dict[str, int]
    extra_events: ExtraEvents
    lethal_modifiers: LethalModifiers

    character_base_price: float
    character_revival_fee: float
    listing_fee: float

    protocol_fee_tiers: Dict[int, float]
    round_delay_enabled: bool = False
    round_delay_min: float = 5.0
    round_delay_max: float = 10.0

    # Allow dict-style access for backward compat with MatchEngine and scripts
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)
