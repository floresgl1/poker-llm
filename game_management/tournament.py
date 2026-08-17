"""
Tournament mode with increasing blinds, multi-table support, and knockout structure.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from game_management.game_config import GameConfig
from game_management.game_runner import GameRunner
from engine.poker_state import GameState, Player
from llm_integration.llm_models import create_llm


logger = logging.getLogger(__name__)


class BlindLevel(Enum):
    """Blind levels for tournament."""
    LEVEL_1 = (1, 2)          # SB 1, BB 2
    LEVEL_2 = (2, 5)          # SB 2, BB 5
    LEVEL_3 = (5, 10)         # SB 5, BB 10
    LEVEL_4 = (10, 25)        # SB 10, BB 25
    LEVEL_5 = (25, 50)        # SB 25, BB 50
    LEVEL_6 = (50, 100)       # SB 50, BB 100
    LEVEL_7 = (100, 200)      # SB 100, BB 200
    LEVEL_8 = (200, 500)      # SB 200, BB 500
    LEVEL_9 = (500, 1000)     # SB 500, BB 1000
    LEVEL_10 = (1000, 2000)   # SB 1000, BB 2000


@dataclass
class TournamentPlayer:
    """Player in a tournament."""
    name: str
    stack: int
    model_id: str
    eliminated: bool = False
    finish_position: Optional[int] = None
    bounties_earned: int = 0


@dataclass
class TournamentStats:
    """Statistics for tournament."""
    session_id: str
    total_players: int
    buy_in: int
    starting_stack: int
    current_level: int = 1
    final_table_size: int = 9
    hand_count: int = 0
    
    # Results
    results: List[Dict] = field(default_factory=list)
    eliminations: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "session_id": self.session_id,
            "total_players": self.total_players,
            "buy_in": f"${self.buy_in}",
            "starting_stack": self.starting_stack,
            "current_level": self.current_level,
            "final_table_size": self.final_table_size,
            "hands_played": self.hand_count,
            "results": self.results,
            "eliminations": self.eliminations,
        }


class Tournament:
    """Tournament runner with increasing blinds and knockout structure."""
    
    def __init__(
        self,
        players_models: List[Tuple[str, str]],  # [(name, model_id), ...]
        buy_in: int = 100,
        starting_stack: int = 1000,
        hands_per_level: int = 5,
        verbose: bool = False
    ):
        """
        Initialize tournament.
        
        Args:
            players_models: List of (player_name, model_id) tuples
            buy_in: Buy-in amount per player
            starting_stack: Starting stack for each player
            hands_per_level: Number of hands before blind increase
            verbose: Print detailed output
        """
        self.players_models = players_models
        self.buy_in = buy_in
        self.starting_stack = starting_stack
        self.hands_per_level = hands_per_level
        self.verbose = verbose
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.tournament_players: Dict[str, TournamentPlayer] = {}
        self.stats = TournamentStats(
            session_id=self.session_id,
            total_players=len(players_models),
            buy_in=buy_in,
            starting_stack=starting_stack,
        )
        
        # Initialize players
        for name, model_id in players_models:
            self.tournament_players[name] = TournamentPlayer(
                name=name,
                stack=starting_stack,
                model_id=model_id
            )
        
        self.button_index = 0
        self.current_level = 1
        self.hands_in_level = 0
    
    def get_blind_level(self, level: int) -> Tuple[int, int]:
        """Get small blind and big blind for a level (2x ratio)."""
        levels = {
            1: (1, 2),
            2: (2, 4),
            3: (5, 10),
            4: (10, 20),
            5: (25, 50),
            6: (50, 100),
            7: (100, 200),
            8: (200, 400),
            9: (500, 1000),
            10: (1000, 2000),
        }
        return levels.get(level, (1000, 2000))
    
    def run_tournament(self, max_hands: Optional[int] = None) -> Dict:
        """
        Run tournament until one player remains.
        
        Args:
            max_hands: Maximum hands to play (for testing)
            
        Returns:
            Tournament results dictionary
        """
        if self.verbose:
            logger.info("\n" + "="*70)
            logger.info("TOURNAMENT START")
            logger.info("="*70)
            self.print_standings()
        
        hand_count = 0
        
        while len([p for p in self.tournament_players.values() if not p.eliminated]) > 1:
            if max_hands and hand_count >= max_hands:
                break
            
            # Check for blind level increase
            if self.hands_in_level >= self.hands_per_level:
                self.current_level += 1
                self.hands_in_level = 0
                
                if self.current_level <= 10:
                    small_blind, big_blind = self.get_blind_level(self.current_level)
                    if self.verbose:
                        logger.info(f"\n>>> BLIND LEVEL UP: Level {self.current_level} "
                                  f"(${small_blind}/${big_blind})")
                else:
                    # Tournament ended
                    break
            
            # Play one hand
            self._play_tournament_hand(hand_count)
            hand_count += 1
            self.hands_in_level += 1
            self.stats.hand_count = hand_count
            
            # Check for eliminations
            active_players = [p for p in self.tournament_players.values() if not p.eliminated]
            if len(active_players) <= 1:
                break
        
        # Finalize tournament
        self._finalize_tournament()
        
        if self.verbose:
            logger.info("\n" + "="*70)
            logger.info("TOURNAMENT COMPLETE")
            logger.info("="*70)
            self.print_final_results()
        
        return self.stats.to_dict()
    
    def _play_tournament_hand(self, hand_num: int) -> None:
        """Play one tournament hand."""
        # Get active players
        active_players = [p for p in self.tournament_players.values() if not p.eliminated]
        
        if len(active_players) < 2:
            return
        
        # Get blinds
        small_blind, big_blind = self.get_blind_level(self.current_level)
        
        # Create game config for this hand
        config = GameConfig(
            num_players=len(active_players),
            starting_stack=self.starting_stack,
            small_blind=small_blind,
            big_blind=big_blind,
            verbose=False
        )
        
        # Create players_models list for GameRunner
        players_models = [
            (player.name, create_llm(player.model_id))
            for player in active_players
        ]
        
        # Create and run game
        runner = GameRunner(config, players_models)
        runner.run_hand(self.button_index % len(active_players))
        
        # Update stacks from game results
        for i, player in enumerate(active_players):
            player.stack = runner.players[i].stack
            
            # Check for elimination
            if player.stack <= 0:
                player.eliminated = True
                player.finish_position = len([p for p in self.tournament_players.values() 
                                             if p.eliminated and p.finish_position]) + 1
                
                self.stats.eliminations.append({
                    "player": player.name,
                    "hand": hand_num,
                    "finish_position": player.finish_position,
                    "final_stack": 0
                })
                
                if self.verbose:
                    logger.info(f"\n!!! {player.name} ELIMINATED (#{player.finish_position})")
        
        # Rotate button
        self.button_index = (self.button_index + 1) % len(active_players)
    
    def _finalize_tournament(self) -> None:
        """Finalize tournament results."""
        remaining_players = [p for p in self.tournament_players.values() if not p.eliminated]
        
        # Assign remaining players
        position = len([p for p in self.tournament_players.values() if p.eliminated and p.finish_position]) + 1
        remaining_players.sort(key=lambda p: p.stack, reverse=True)
        
        for player in remaining_players:
            player.finish_position = position
            position += 1
        
        # Create results list
        all_players = sorted(
            self.tournament_players.values(),
            key=lambda p: p.finish_position
        )
        
        for rank, player in enumerate(all_players, 1):
            self.stats.results.append({
                "finish_position": rank,
                "player_name": player.name,
                "model": player.model_id,
                "final_stack": player.stack,
                "profit_loss": player.stack - self.starting_stack,
            })
    
    def print_standings(self) -> None:
        """Print current standings."""
        active_players = sorted(
            [p for p in self.tournament_players.values() if not p.eliminated],
            key=lambda p: p.stack,
            reverse=True
        )
        
        small_blind, big_blind = self.get_blind_level(self.current_level)
        
        print(f"\n{'='*70}")
        print(f"LEVEL {self.current_level}: Blinds ${small_blind}/${big_blind}")
        print(f"Hand: {self.stats.hand_count}")
        print(f"{'='*70}")
        print(f"{'Rank':<6} {'Player':<20} {'Stack':<12} {'BB Depth':<12} {'Model':<15}")
        print("-"*70)
        
        for rank, player in enumerate(active_players, 1):
            bb_depth = f"{player.stack // big_blind:.1f}x"
            print(f"{rank:<6} {player.name:<20} ${player.stack:<11} {bb_depth:<12} "
                  f"{player.model_id:<15}")
        
        eliminated = [p for p in self.tournament_players.values() if p.eliminated]
        if eliminated:
            print(f"\nEliminated: {', '.join([p.name for p in eliminated])}")
        
        print()
    
    def print_final_results(self) -> None:
        """Print final tournament results."""
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"{'Position':<12} {'Player':<20} {'Model':<15} {'Stack':<12} {'Profit/Loss':<12}")
        print("-"*70)
        
        for result in self.stats.results:
            position = result["finish_position"]
            name = result["player_name"]
            model = result["model"]
            stack = result["final_stack"]
            profit = result["profit_loss"]
            
            profit_str = f"${profit:+.0f}"
            print(f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th':<10} "
                  f"{name:<20} {model:<15} ${stack:<11} {profit_str:<12}")
        
        print("="*70 + "\n")
    
    def export_results(self, filename: str) -> None:
        """
        Export tournament results to JSON.
        
        Args:
            filename: Output filename
        """
        results = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "tournament": {
                "buy_in": self.buy_in,
                "starting_stack": self.starting_stack,
                "total_players": len(self.players_models),
                "hands_played": self.stats.hand_count,
                "hands_per_level": self.hands_per_level,
            },
            "players": [
                asdict(p) for p in self.tournament_players.values()
            ],
            "results": self.stats.results,
            "eliminations": self.stats.eliminations,
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        if self.verbose:
            logger.info(f"Tournament results exported to {filename}")
