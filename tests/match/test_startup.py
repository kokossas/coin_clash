"""
Test script for Coin Clash match startup logic.
This script demonstrates how the match startup conditions work.
"""

import logging
import sys
import datetime
import time
from sqlalchemy.orm import Session

# Use absolute imports since we're outside the core package
from coin_clash.core.database.models import init_db
from coin_clash.core.database.db import get_session
from coin_clash.core.player.repository import SqlPlayerRepo
from coin_clash.core.player.character_repository import SqlCharacterRepo
from coin_clash.core.player.item_repository import SqlItemRepo
from coin_clash.core.match.repository import SqlMatchRepo
from coin_clash.core.match.event_repository import SqlEventRepo
from coin_clash.core.match.service import MatchService
from coin_clash.core.player.service import CharacterService
from coin_clash.core.scheduler.scheduler import scheduler
from coin_clash.core.config.config_loader import load_config
from coin_clash.core.common.exceptions import InsufficientBalanceError, MatchAlreadyActiveError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_services(db_session: Session) -> tuple:
    """Create service instances with the given DB session."""
    player_repo = SqlPlayerRepo(db_session)
    character_repo = SqlCharacterRepo(db_session)
    match_repo = SqlMatchRepo(db_session)
    event_repo = SqlEventRepo(db_session)
    item_repo = SqlItemRepo(db_session)
    
    match_service = MatchService(
        match_repo=match_repo,
        player_repo=player_repo,
        character_repo=character_repo,
        db_session=db_session
    )
    
    character_service = CharacterService(
        player_repo=player_repo,
        character_repo=character_repo,
        match_repo=match_repo,
        match_service=match_service,
        db_session=db_session
    )
    
    return player_repo, character_repo, match_repo, match_service, character_service

def match_service_factory():
    """Factory function for creating a MatchService with a fresh DB session."""
    session = next(get_session())
    player_repo = SqlPlayerRepo(session)
    character_repo = SqlCharacterRepo(session)
    match_repo = SqlMatchRepo(session)
    
    return MatchService(
        match_repo=match_repo,
        player_repo=player_repo,
        character_repo=character_repo,
        db_session=session
    )

def test_startup_with_player_cap():
    """Test match startup when player cap is reached and all have purchased."""
    logger.info("Starting test: Match startup with player cap")
    
    with next(get_session()) as session:
        player_repo, character_repo, match_repo, match_service, character_service = create_services(session)
        
        # Create players with initial balance
        players = []
        for i in range(3):
            player = player_repo.get_or_create_player(f"player_{i}")
            player_repo.update_player_balance(player.id, 100.0)  # Give them funds
            players.append(player)
        
        # Create a match with cap of 3 players
        match = match_service.create_match(
            entry_fee=10.0,
            kill_award_rate=0.5,
            start_method="cap",
            start_threshold=3  # Cap of 3 players
        )
        
        session.commit()
        
        logger.info(f"Created match with ID {match.id}")
        
        # Have all players join and purchase characters
        for i, player in enumerate(players):
            try:
                character = character_service.purchase_character(
                    username=player.username,
                    match_id=match.id,
                    character_name=f"Character_{player.username}"
                )
                logger.info(f"Player {player.username} joined with character {character.name}")
            except Exception as e:
                logger.error(f"Error purchasing character: {str(e)}")
        
        # Check if match started (should have started after last player joined)
        match = match_repo.get_match_by_id(match.id)
        logger.info(f"Match status: {match.status}")
        
        if match.status == "active":
            logger.info("✅ Test successful: Match started when player cap reached and all purchased")
        else:
            logger.error("❌ Test failed: Match did not start when conditions were met")

def test_startup_with_timer():
    """Test match startup when timer expires."""
    logger.info("Starting test: Match startup with timer")
    
    with next(get_session()) as session:
        player_repo, character_repo, match_repo, match_service, character_service = create_services(session)
        
        # Create players with initial balance
        players = []
        for i in range(5):
            player = player_repo.get_or_create_player(f"timer_player_{i}")
            player_repo.update_player_balance(player.id, 100.0)  # Give them funds
            players.append(player)
        
        # Create a match with 5 second timer
        match = match_service.create_match(
            entry_fee=10.0,
            kill_award_rate=0.5,
            start_method="timeout",
            start_threshold=5  # 5 second timer
        )
        
        session.commit()
        
        logger.info(f"Created match with ID {match.id} with 5 second timer")
        
        # Schedule the match to start when timer expires
        timer_end = match.start_timer_end
        scheduler.schedule_match_start(match.id, timer_end, match_service_factory)
        
        # Have only some players join and purchase characters
        for i, player in enumerate(players[:3]):  # Only first 3 players join
            try:
                character = character_service.purchase_character(
                    username=player.username,
                    match_id=match.id,
                    character_name=f"Character_{player.username}"
                )
                logger.info(f"Player {player.username} joined with character {character.name}")
            except Exception as e:
                logger.error(f"Error purchasing character: {str(e)}")
        
        # Wait for timer to expire
        logger.info(f"Waiting for timer to expire at {timer_end}")
        now = datetime.datetime.now(datetime.timezone.utc)
        sleep_time = (timer_end - now).total_seconds() + 1
        time.sleep(max(1, sleep_time))
        
        # Check if match started
        match = match_repo.get_match_by_id(match.id)
        logger.info(f"Match status after timer expiry: {match.status}")
        
        # Count auto-assigned characters
        characters = session.query(character_repo.__class__.__class__).filter_by(match_id=match.id).all()
        logger.info(f"Total characters in match: {len(characters)}")
        
        if match.status == "active":
            logger.info("✅ Test successful: Match started when timer expired")
        else:
            logger.error("❌ Test failed: Match did not start when timer expired")

def main():
    """Run the startup logic tests."""
    # Initialize DB if needed
    init_db()
    
    # Start the scheduler
    scheduler.start()
    
    try:
        # Run tests
        test_startup_with_player_cap()
        print("\n")
        test_startup_with_timer()
    finally:
        # Stop the scheduler
        scheduler.stop()

if __name__ == "__main__":
    main()
