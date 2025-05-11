# /home/ubuntu/coin_clash/core/common/utils.py

import random
from typing import Optional, TypeVar, List

T = TypeVar('T')

class SeedableRandom:
    """A wrapper around random.Random for seedable randomness."""
    def __init__(self, seed: Optional[int] = None):
        self._random = random.Random()
        if seed is not None:
            self.seed(seed)

    def seed(self, seed: int):
        self._random.seed(seed)

    def choice(self, seq: List[T]) -> T:
        return self._random.choice(seq)

    def sample(self, population: List[T], k: int) -> List[T]:
        return self._random.sample(population, k)

    def choices(self, population: List[T], weights: Optional[List[float]] = None, k: int = 1) -> List[T]:
        return self._random.choices(population, weights=weights, k=k)

    def uniform(self, a: float, b: float) -> float:
        return self._random.uniform(a, b)

    def randint(self, a: int, b: int) -> int:
        return self._random.randint(a, b)

    def random(self) -> float:
        """Return the next random floating point number in the range [0.0, 1.0)."""
        return self._random.random()

# Character Naming Utility
# Using a predefined list as suggested, though GameLogic mentioned cycling
# pasted_content mentioned sequential assignment based on global index pointer.
# Let's go with sequential assignment for simplicity and persistence.
# We'll manage the index pointer within the player creation logic later.
CHARACTER_NAMES = [
    "Ace", "Bandit", "Calamity", "Deadeye", "Echo", "Flint", "Ghost", "Hazard",
    "Inferno", "Jinx", "Kestrel", "Lasso", "Maverick", "Nomad", "Outlaw", "Phantom",
    "Quicksilver", "Rattler", "Shadow", "Tumbleweed", "Umbra", "Viper", "Whisper", "Xylo",
    "Yonder", "Zephyr", "Anchor", "Blaze", "Coral", "Drift", "Eddy", "Fin", "Gale",
    "Harbor", "Isle", "Jetty", "Kelp", "Lagoon", "Marina", "Nautilus", "Oceanus",
    "Pearl", "Quay", "Reef", "Starfish", "Tide", "Undertow", "Voyager", "Wave",
    "Xebec", "Yardarm", "Zenith"
]

# Track name usages for character name generation
_name_index = 0

def get_next_character_name() -> str:
    """
    Get the next available character name from the predefined list.
    Names will cycle if more are needed than available in the list.
    
    Returns:
        str: A character name
    """
    global _name_index
    name = CHARACTER_NAMES[_name_index % len(CHARACTER_NAMES)]
    _name_index += 1
    return name

# Global index pointer for character names (will be managed by the part creating characters)
# This simple approach might have issues with concurrency if scaled, but fine for simulation.
# A better approach might involve a dedicated sequence in the DB.
_character_name_index = 0

def get_next_character_name() -> str:
    global _character_name_index
    name = CHARACTER_NAMES[_character_name_index % len(CHARACTER_NAMES)]
    _character_name_index += 1
    # Maybe add the index to make it unique if list repeats often?
    # For now, just cycle.
    return name


