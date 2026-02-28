import re
import time
import logging
from typing import List, Dict, Any, Optional

from backend.app.models.models import Character, OwnedCharacter
from ..player.repository import PlayerRepo
from ..player.character_repository import CharacterRepo
from ..player.item_repository import ItemRepo
from .repository import MatchRepo
from .event_repository import EventRepo
from .scenario_loader import EVENT_TYPE_TO_CATEGORY
from ..common.utils import SeedableRandom
from ..common.exceptions import InsufficientParticipantsError, CriticalMatchError, SkipEvent

logger = logging.getLogger(__name__)

class MatchEngine:
    def __init__(self,
                 match_id: int,
                 config: Dict[str, Any],
                 scenarios: Dict[str, List[Dict[str, str]]],
                 player_repo: PlayerRepo,
                 character_repo: CharacterRepo,
                 match_repo: MatchRepo,
                 event_repo: EventRepo,
                 item_repo: ItemRepo,
                 random_seed: Optional[int] = None):
         # map event types → their effect‐handler methods
        self._effect_handlers = {
            "direct_kill":          self._handle_direct_kill,
            "self":                 self._handle_self_event,
            "environmental":        self._handle_environmental_event,
            "group":                self._handle_group_event,
            "extra_lethal":         self._handle_extra_lethal_event,
            "comeback":             self._handle_comeback_event,
            "story":                self._handle_story_event,
            "non_lethal_story":     self._handle_story_event,
        }

        self.config = config
        self.scenarios = scenarios
        self.player_repo = player_repo
        self.character_repo = character_repo
        self.match_repo = match_repo
        self.event_repo = event_repo
        self.item_repo = item_repo
        self.random = SeedableRandom(random_seed)

        self.match = self.match_repo.get_match_by_id(match_id)
        if not self.match:
            raise CriticalMatchError(f"Match with ID {match_id} not found.")

        self.match_id = match_id
        self.entry_fee = self.match.entry_fee
        self.kill_award_rate = self.match.kill_award_rate

        # Initial state loaded from DB or passed in
        self.participants: List[Character] = [] # Characters participating in this match
        self.alive_pool: Dict[int, Character] = {}
        self.dead_pool: Dict[int, Character] = {}
        self.round_number = 0
        self.match_log: List[str] = [] # Simple text log for printing simulation

        logger.info(
            "engine_initialized",
            extra={"match_id": self.match_id, "seed": random_seed}
        )

    def _log_event(self, event_type: str, scenario_source: str, scenario_text: str, affected_characters: List[Character]):
        """Logs event to DB and internal log."""
        affected_ids_str = ",".join(map(str, [c.id for c in affected_characters]))
        self.event_repo.create_match_event(
            match_id=self.match_id,
            round_number=self.round_number,
            event_type=event_type,
            scenario_source=scenario_source,
            scenario_text=scenario_text,
            affected_character_ids=affected_ids_str
        )
        self.match_log.append(f"Round {self.round_number}: [{event_type.upper()}] {scenario_text}")
        logger.info(
            "event_logged",
            extra={
                "match_id": self.match_id,
                "round": self.round_number,
                "event_type": event_type,
                "scenario_id": scenario_source,
                "scenario_text": scenario_text,
                "participants": [c.id for c in affected_characters]
            }
        )

    def _get_placeholder_count(self, text: str) -> int:
        """Counts unique placeholders like [Character A], [Character B] etc."""
        placeholders = set(re.findall(r"\[Character ([A-Z])\]", text))
        return len(placeholders)

    def _select_participants(self, count: int, source_pool: Dict[int, Character]) -> List[Character]:
        """Selects distinct participants uniformly from the given pool."""
        if not source_pool or len(source_pool) < count:
            from ..common.exceptions import SkipEvent
            raise SkipEvent(f"Not enough participants ({len(source_pool)}) for selection of {count}")
        selected_ids = self.random.sample(list(source_pool.keys()), k=count)
        return [source_pool[id] for id in selected_ids]

    def _substitute_placeholders(self, text: str, participants: List[Character]) -> str:
        """Substitutes [Character A], [B]... with participant display names.
        If there aren’t enough participants, raises InsufficientParticipantsError."""
        substituted_text = text
        placeholders = sorted(set(re.findall(r"(\[Character [A-Z]\])", text)))
        if len(participants) < len(placeholders):
            raise InsufficientParticipantsError(
                f"{len(participants)} participants for {len(placeholders)} placeholders in '{text}'"
            )
        for i, placeholder in enumerate(placeholders):
            substituted_text = substituted_text.replace(placeholder, participants[i].display_name, 1)
 
        return substituted_text

    def _apply_elimination(self, character: Character):
        """Moves a character from alive to dead pool and updates DB."""
        if character.id in self.alive_pool:
            char_id = character.id
            self.dead_pool[char_id] = self.alive_pool.pop(char_id)
            self.character_repo.update_character_status(char_id, is_alive=False)
            logger.info(
              "character_eliminated",
                extra={"match_id": self.match_id, "round": self.round_number, "character_id": char_id}
            )
        else:
            logger.warning(
                "elimination_failed_not_alive",
                extra={
                    "match_id": self.match_id,
                    "round": self.round_number,
                    "character_id": character.id,
                    "character_name": character.display_name
                }
            )

    def _apply_revival(self, character: Character):
        """Moves a character from dead to alive pool and updates DB."""
        if character.id in self.dead_pool:
            char_id = character.id
            self.alive_pool[char_id] = self.dead_pool.pop(char_id)
            self.character_repo.update_character_status(char_id, is_alive=True)
            logger.info(
                "character_revived",
                extra={"match_id": self.match_id, "round": self.round_number, "character_id": char_id}
            )
        else:
            logger.warning(
                "revival_failed_not_dead",
                extra={
                    "match_id": self.match_id,
                    "round": self.round_number,
                    "character_id": character.id,
                    "character_name": character.display_name
                }
            )

    def _handle_direct_kill(self, participants: List[Character]):
        # participants[0]=killer, participants[1]=victim
        if len(participants) >= 2:
            victim, killer = participants[1], participants[0]
            self._apply_elimination(victim)
            player = self.player_repo.get_player_by_id(killer.player_id)
            if player:
                self.player_repo.add_kill(player.id)

    def _handle_self_event(self, participants: List[Character]):
        # participants[0] is self-eliminated
        if participants:
            self._apply_elimination(participants[0])

    def _handle_environmental_event(self, participants: List[Character]):
        # participants[0] is eliminated
        if participants:
            self._apply_elimination(participants[0])

    def _handle_group_event(self, participants: List[Character]):
        # both participants eliminated
        if len(participants) >= 2:
            self._apply_elimination(participants[0])
            self._apply_elimination(participants[1])

    def _handle_extra_lethal_event(self, participants: List[Character]):
        if participants:
            self._apply_elimination(participants[0])

    def _handle_comeback_event(self, participants: List[Character]):
        if participants:
            self._apply_revival(participants[0])

    def _handle_story_event(self, participants: List[Character]):
        logger.debug(
            "story_no_pool_change",
            extra={"match_id": self.match_id, "round": self.round_number}
        )


    def _process_event(self, event_type: str):
        """Handles a single event: sampling, substitution, application, logging."""
        logger.debug(
            "processing_event_type",
            extra={
            "match_id":    self.match_id,
            "round":       self.round_number,
            "event_type":  event_type
            }
        )
        is_lethal = event_type in ["direct_kill", "self", "environmental", "group", "extra_lethal"]
        is_comeback = event_type == "comeback"
        is_story = event_type in ["story", "non_lethal_story"]

        # --- Determine Scenario Category --- 
        category_source = EVENT_TYPE_TO_CATEGORY.get(event_type)
        if isinstance(category_source, list): # Handle extra_lethal pulling from multiple
            category = self.random.choice(category_source)
        else:
            category = category_source

        if not category or not self.scenarios.get(category):
            # Handle cases with no scenarios (e.g., maybe comeback is just text)
            if is_comeback and self.dead_pool:
                 # Select character to revive
                revived_char = self.random.choice(list(self.dead_pool.values()))
                scenario_text = f"{revived_char.display_name} claws their way back from the brink!"
                scenario_source_log = "generated_comeback"
                affected_chars = [revived_char]
                self._apply_revival(revived_char)
                self._log_event(event_type, scenario_source_log, scenario_text, affected_chars)
                return # Handled comeback without scenario file
            else:
                logger.warning(
                    "missing_scenario_category",
                    extra={
                        "match_id": self.match_id,
                        "round": self.round_number,
                        "event_type": event_type,
                        "category": category
                    }
                )
                return

        # --- Sample Scenario --- 
        available_scenarios = self.scenarios[category]
        if not available_scenarios:
             logger.warning(
                "scenario_list_empty",
                extra={
                    "match_id": self.match_id,
                    "round": self.round_number,
                    "category": category
                }
            )
             return
        chosen_scenario = self.random.choice(available_scenarios)
        scenario_text_template = chosen_scenario["text"]
        scenario_id = chosen_scenario.get("id", f"unknown_{category}")

        # --- Select Participants --- 
        placeholder_count = self._get_placeholder_count(scenario_text_template)
        participants = []
        if is_comeback:
            if self.dead_pool:
                try:
                    participants = self._select_participants(1, self.dead_pool)
                except SkipEvent as se:
                    logger.info(
                        "event_skipped",
                        extra={
                            "match_id":    self.match_id,
                            "round":       self.round_number,
                            "event_type":  event_type,
                            "scenario_id": scenario_id,
                            "reason":      str(se),
                        }
                    )
                    return
            else:
                logger.debug(
                    "comeback_no_dead_pool",
                    extra={
                        "match_id":   self.match_id,
                        "round":      self.round_number,
                        "event_type": event_type
                    }
                )
                return
        elif placeholder_count > 0:
            try:
                participants = self._select_participants(placeholder_count, self.alive_pool)
            except SkipEvent as se:
                logger.info(
                    "event_skipped",
                    extra={
                        "match_id":    self.match_id,
                        "round":       self.round_number,
                        "event_type":  event_type,
                        "scenario_id": scenario_id,
                        "needed":      placeholder_count,
                        "available":   len(self.alive_pool),
                        "reason":      str(se),
                    }
                )
                return
        
        # If not enough participants could be selected (e.g., pool too small)
        if placeholder_count > 0 and len(participants) < placeholder_count:
            # (fallback guard in case _select_participants ever returns partial lists)
            logger.info(
                "event_skipped",
                extra={
                    "match_id":    self.match_id,
                    "round":       self.round_number,
                    "event_type":  event_type,
                    "scenario_id": scenario_id,
                    "needed":      placeholder_count,
                    "got":         len(participants),
                    "reason":      "post-selection check",
                }
            )
            return

        # --- Substitute and Log --- 
        # Try to substitute; if placeholders > participants, skip the event
        try:
            final_scenario_text = self._substitute_placeholders(
                scenario_text_template,
                participants
            )
        except SkipEvent as se:
            logger.info("event_skipped", extra={"match_id": self.match_id, "round": self.round_number, "reason": str(se)})
            return
 
        self._log_event(event_type, scenario_id, final_scenario_text, participants)

        # --- Apply Effects --- 
        # Effects depend on event_type, not placeholder roles (A vs B)
        handler = self._effect_handlers.get(event_type)
        if handler:
            handler(participants)

    def _run_round(self):
        """Runs a single round of the match."""
        self.round_number += 1
        logger.info(
            "round_started",
            extra={"match_id": self.match_id, "round": self.round_number, "alive": len(self.alive_pool)}
        )
        self.match_log.append(f"\n--- Round {self.round_number} ({len(self.alive_pool)} alive) ---")

        if len(self.alive_pool) <= 1:
            logger.warning(
                "round_too_few_alive_at_start",
                extra={
                    "match_id":   self.match_id,
                    "round":      self.round_number,
                    "alive_count": len(self.alive_pool)
                }
            )
            return

        # Check special rule: 2 characters remaining
        two_remain = len(self.alive_pool) == 2

        # 1. Primary Event
        primary_weights = self.config["primary_event_weights"]
        allowed_primary_events = list(primary_weights.keys())
        if two_remain:
            # Remove group eliminations if only 2 remain
            allowed_primary_events = [e for e in allowed_primary_events if e != "group"]
            if not allowed_primary_events:
                 logger.error(
                    "no_primary_events_when_two_remain",
                    extra={"match_id": self.match_id, "round": self.round_number}
                )
                 return # Avoid infinite loop or error
            
            # Adjust weights proportionally if needed (or just re-normalize)
            current_weights = [primary_weights[e] for e in allowed_primary_events]
            total_weight = sum(current_weights)
            normalized_weights = [w / total_weight for w in current_weights] if total_weight > 0 else None
        else:
            allowed_primary_events = list(primary_weights.keys())
            normalized_weights = [w / 100.0 for w in primary_weights.values()] # Assuming weights sum to 100

        if normalized_weights:
            primary_event_type = self.random.choices(allowed_primary_events, weights=normalized_weights, k=1)[0]
            logger.debug("primary_event_chosen", extra={"match_id": self.match_id, "round": self.round_number, "event_type": primary_event_type})
            self._process_event(primary_event_type)
        else:
            logger.error(
                "primary_weight_lookup_failed",
                extra={"match_id": self.match_id, "round": self.round_number}
            )

        # Check if match ended mid-round
        if len(self.alive_pool) <= 1:
            return

        # 2. Additional Events (checked independently)
        extra_config = self.config["extra_events"]

        # 2a. Extra Non-Lethal Story
        if self.random.random() < extra_config["non_lethal_story_chance"]:
            logger.debug(
            "extra_non_lethal_story_triggered",
            extra={"match_id": self.match_id, "round": self.round_number}
            )
            self._process_event("non_lethal_story")
            if len(self.alive_pool) <= 1: return

        # 2b. Extra Lethal
        if not two_remain: # Cannot occur if only 2 remain
            lethal_chance = extra_config["extra_lethal_base_chance"]
            if len(self.alive_pool) > 12:
                lethal_chance += self.config["lethal_modifiers"]["cap_12_plus"]
            elif len(self.alive_pool) > 8:
                lethal_chance += self.config["lethal_modifiers"]["cap_8_plus"]
            
            if self.random.random() < lethal_chance:
                logger.debug(
                "extra_lethal_triggered",
                extra={"match_id": self.match_id, "round": self.round_number}
                )
                self._process_event("extra_lethal")
                if len(self.alive_pool) <= 1: return

        # 2c. Comeback
        if self.dead_pool: # Cannot occur if dead pool is empty
            if self.random.random() < extra_config["comeback_base_chance"]:
                logger.debug(
                "extra_comeback_triggered",
                extra={"match_id": self.match_id, "round": self.round_number}
                )
                self._process_event("comeback")
                # No need to check alive pool count here, comeback increases it
        
        logger.info(
            "round_ended",
            extra={"match_id": self.match_id, "round": self.round_number, "alive": len(self.alive_pool)}
        )


    def run_match(self, participants: List[Character]):
        """Runs the full match simulation."""
        logger.info(
            "match_started",
            extra={
                "match_id": self.match_id,
                "participants": len(participants)
            }
        )
        self.match_log.append(f"Match {self.match_id} Started with {len(participants)} participants.")
        self.participants = participants
        self.alive_pool = {char.id: char for char in participants}
        self.dead_pool = {}
        self.round_number = 0

        # Update match status and start time in DB
        self.match_repo.update_match_status(self.match_id, "active")
        self.match_repo.set_match_start_time(self.match_id)

        while len(self.alive_pool) > 1:
            self._run_round()
            if self.config.get("round_delay_enabled"):
                delay = self.random.uniform(
                    self.config.get("round_delay_min", 5.0),
                    self.config.get("round_delay_max", 10.0),
                )
                time.sleep(delay)

        # --- Match End --- 
        winner = None
        if len(self.alive_pool) == 1:
            winner_id = list(self.alive_pool.keys())[0]
            winner = self.alive_pool[winner_id]
            logger.info(
                "match_ended",
                extra={
                    "match_id": self.match_id,
                    "winner_id": winner.id,
                    "winner_name": winner.display_name
                }
            )
            self.match_log.append(f"\n--- Match Over --- Winner: {winner.display_name} ---")

            # Update winner stats
            winner_player = self.player_repo.get_player_by_id(winner.player_id)
            if winner_player:
                self.player_repo.add_win(winner_player.id)

            # Update match record in DB
            self.match_repo.set_match_winner(self.match_id, winner.id)

        else:
            logger.error(
                "match_ended_without_winner",
                extra={
                    "match_id": self.match_id,
                    "alive_count": len(self.alive_pool)
                }
            )
            self.match_log.append("\n--- Match Over --- Error: No single winner! ---")

        # Update match status and end time
        self.match_repo.update_match_status(self.match_id, "completed")
        self.match_repo.set_match_end_time(self.match_id)

        # Sync match_characters → owned_characters
        all_characters = list(self.alive_pool.values()) + list(self.dead_pool.values())
        for char in all_characters:
            if char.owned_character_id is not None:
                owned = (
                    self.character_repo.db.query(OwnedCharacter)
                    .filter(OwnedCharacter.id == char.owned_character_id)
                    .first()
                )
                if owned is not None:
                    owned.is_alive = char.is_alive
                    owned.last_match_id = self.match_id

        return winner, self.match_log