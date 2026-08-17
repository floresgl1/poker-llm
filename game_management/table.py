from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

from engine.poker_state import Player
from llm_integration.llm_interface import LLMInterface
from game_management.game_config import GameConfig
from game_management.game_runner import GameRunner


class Table:
    """Manages a complete poker session with multiple hands."""
    
    def __init__(self, config: GameConfig, players_with_models: List[Tuple[str, LLMInterface]], 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize poker table.
        
        Args:
            config: GameConfig instance
            players_with_models: List of (player_name, llm_model) tuples
            logger: Optional logger instance
        """
        self.config = config
        self.players_with_models = players_with_models
        self.logger = logger or self._setup_logger()
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.hands_played = 0
        self.button_position = 0
        
        # Game runner
        self.game_runner = GameRunner(config, players_with_models, logger)
        
        # Statistics tracking
        self.hand_history: List[Dict] = []
        self.player_stats: Dict[str, Dict] = {
            name: {
                'hands': 0,
                'wins': 0,
                'buy_ins': 1,
                'final_stack': config.starting_stack,
                'max_stack': config.starting_stack,
                'min_stack': config.starting_stack,
            }
            for name, _ in players_with_models
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger."""
        logger = logging.getLogger('PokerTable')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def run_session(self, num_hands: Optional[int] = None) -> Dict:
        """
        Run a complete poker session.
        
        Args:
            num_hands: Number of hands to play (uses config.max_hands if None)
        
        Returns:
            Session statistics dictionary
        """
        max_hands = num_hands or self.config.max_hands or 100
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"POKER SESSION {self.session_id}")
        self.logger.info(f"Config: {self.config.num_players}p, "
                        f"${self.config.starting_stack} stacks, "
                        f"${self.config.small_blind}/{self.config.big_blind} blinds")
        self.logger.info(f"{'='*60}\n")
        
        # Reset models for new session
        for _, model in self.players_with_models:
            model.reset()
        
        try:
            for hand_num in range(1, max_hands + 1):
                # Run hand
                winner = self.game_runner.run_hand(button_idx=self.button_position)
                
                # Update statistics
                if winner:
                    self._update_hand_stats(winner)
                
                # Check for eliminated players
                if self._check_game_end():
                    self.logger.info(f"\nSession ended: Only one player remains")
                    break
                
                # Move button
                self.button_position = (self.button_position + 1) % len(self.game_runner.players)
                self.hands_played += 1
                
                # Print current standings
                if hand_num % 5 == 0:
                    self._print_standings()
        
        except KeyboardInterrupt:
            self.logger.info("Session interrupted by user")
        
        return self.get_session_results()
    
    def run_single_hand(self) -> Optional[str]:
        """Run a single hand and return winner."""
        winner = self.game_runner.run_hand(button_idx=self.button_position)
        
        if winner:
            self._update_hand_stats(winner)
            self.button_position = (self.button_position + 1) % len(self.game_runner.players)
            self.hands_played += 1
        
        return winner
    
    def _update_hand_stats(self, winner: str):
        """Update statistics for a completed hand."""
        # Find winner index
        winner_idx = None
        for i, (name, _) in enumerate(self.players_with_models):
            if name == winner:
                winner_idx = i
                break
        
        if winner_idx is None:
            return
        
        # Update stats
        for i, player in enumerate(self.game_runner.players):
            name = player.name
            self.player_stats[name]['hands'] += 1
            self.player_stats[name]['final_stack'] = player.stack
            self.player_stats[name]['max_stack'] = max(self.player_stats[name]['max_stack'], player.stack)
            self.player_stats[name]['min_stack'] = min(self.player_stats[name]['min_stack'], player.stack)
            
            if name == winner:
                self.player_stats[name]['wins'] += 1
        
        # Record hand
        self.hand_history.append({
            'hand_number': self.game_runner.hand_number,
            'winner': winner,
            'pot': self.game_runner.game_state.pot if self.game_runner.game_state else 0,
            'stacks': {name: player.stack for name, player in zip(
                [n for n, _ in self.players_with_models],
                self.game_runner.players
            )},
        })
    
    def _check_game_end(self) -> bool:
        """Check if game should end (only 1 player left)."""
        active_count = sum(1 for player in self.game_runner.players if player.stack > 0)
        return active_count <= 1
    
    def _print_standings(self):
        """Print current game standings."""
        self.logger.info(f"\n--- STANDINGS AFTER HAND {self.hands_played} ---")
        
        # Sort by stack
        standings = sorted(
            [(name, self.player_stats[name]['final_stack'], self.player_stats[name]['wins']) 
             for name, _ in self.players_with_models],
            key=lambda x: x[1],
            reverse=True
        )
        
        for rank, (name, stack, wins) in enumerate(standings, 1):
            self.logger.info(f"{rank}. {name:20s} Stack: ${stack:6d}  Wins: {wins}")
    
    def get_session_results(self) -> Dict:
        """Get complete session results."""
        standings = sorted(
            [(name, stats['final_stack'], stats['wins'], stats['hands'], stats['max_stack'], stats['min_stack'])
             for name, stats in self.player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        results = {
            'session_id': self.session_id,
            'config': self.config.to_dict(),
            'hands_played': self.hands_played,
            'total_pot_distributed': sum(h['pot'] for h in self.hand_history),
            'standings': [],
            'hand_history': self.hand_history,
        }
        
        for rank, (name, final_stack, wins, hands, max_stack, min_stack) in enumerate(standings, 1):
            buy_in = self.config.starting_stack * self.player_stats[name]['buy_ins']
            profit = final_stack - buy_in
            win_rate = (wins / hands * 100) if hands > 0 else 0
            
            results['standings'].append({
                'rank': rank,
                'name': name,
                'final_stack': final_stack,
                'profit': profit,
                'buy_ins': self.player_stats[name]['buy_ins'],
                'hands_played': hands,
                'wins': wins,
                'win_rate': win_rate,
                'max_stack': max_stack,
                'min_stack': min_stack,
            })
        
        return results
    
    def print_results(self):
        """Print formatted session results."""
        results = self.get_session_results()
        
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"SESSION RESULTS - {results['session_id']}")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"Hands played: {results['hands_played']}")
        self.logger.info(f"Total distributed: ${results['total_pot_distributed']}\n")
        
        for standing in results['standings']:
            self.logger.info(
                f"{standing['rank']}. {standing['name']:20s} "
                f"${standing['final_stack']:6d} "
                f"(+${standing['profit']:6d}) "
                f"Wins: {standing['wins']:2d}/{standing['hands_played']:2d} "
                f"({standing['win_rate']:5.1f}%)"
            )
        
        self.logger.info(f"{'='*70}\n")
    
    def export_hand_history(self, filename: str):
        """Export hand history to file."""
        import json
        
        results = self.get_session_results()
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Hand history exported to {filename}")
