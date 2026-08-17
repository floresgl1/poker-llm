"""
Model comparison framework for A/B testing different LLM models.
Tracks performance metrics and generates comparison reports.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from game_management.game_config import GameConfig
from game_management.table import Table
from llm_integration.llm_models import create_llm


logger = logging.getLogger(__name__)


@dataclass
class ModelStats:
    """Statistics for a single model."""
    model_id: str
    hands_played: int = 0
    wins: int = 0
    total_profit: float = 0.0
    avg_stack: float = 0.0
    max_stack: float = 0.0
    min_stack: float = 0.0
    
    # Positional stats
    position_stats: Dict[str, Dict] = field(default_factory=dict)
    
    # Head-to-head records
    h2h_records: Dict[str, Dict] = field(default_factory=lambda: defaultdict(
        lambda: {"wins": 0, "losses": 0, "ties": 0}
    ))
    
    @property
    def win_rate(self) -> float:
        """Win rate as percentage."""
        if self.hands_played == 0:
            return 0.0
        return (self.wins / self.hands_played) * 100
    
    @property
    def roi(self) -> float:
        """Return on investment as percentage."""
        if self.hands_played == 0:
            return 0.0
        # Assuming standard $300 buy-in
        return (self.total_profit / (self.hands_played * 10)) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "model_id": self.model_id,
            "hands_played": self.hands_played,
            "wins": self.wins,
            "win_rate": f"{self.win_rate:.1f}%",
            "total_profit": f"${self.total_profit:.2f}",
            "roi": f"{self.roi:.1f}%",
            "avg_stack": f"${self.avg_stack:.2f}",
            "max_stack": f"${self.max_stack:.2f}",
            "min_stack": f"${self.min_stack:.2f}",
            "h2h_records": {k: v for k, v in self.h2h_records.items()},
        }


class ModelComparison:
    """Framework for comparing LLM models in poker matches."""
    
    def __init__(self, config: GameConfig, verbose: bool = False):
        """
        Initialize comparison framework.
        
        Args:
            config: Game configuration
            verbose: Print detailed output
        """
        self.config = config
        self.verbose = verbose
        self.models: Dict[str, str] = {}  # model_id -> model_name
        self.stats: Dict[str, ModelStats] = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.matches: List[Dict] = []
    
    def add_model(self, model_id: str, model_name: Optional[str] = None) -> None:
        """
        Add a model to the comparison.
        
        Args:
            model_id: Model identifier (e.g., 'random', 'call_any', 'claude', 'gpt4')
            model_name: Display name (defaults to model_id)
        """
        self.models[model_id] = model_name or model_id
        if model_id not in self.stats:
            self.stats[model_id] = ModelStats(model_id=model_id)
        if self.verbose:
            logger.info(f"Added model: {model_id}")
    
    def run_head_to_head(self, model1_id: str, model2_id: str, num_hands: int = 10) -> Dict:
        """
        Run head-to-head match between two models.
        
        Args:
            model1_id: First model ID
            model2_id: Second model ID
            num_hands: Number of hands to play
            
        Returns:
            Match results dictionary
        """
        if model1_id not in self.models:
            raise ValueError(f"Model {model1_id} not added to comparison")
        if model2_id not in self.models:
            raise ValueError(f"Model {model2_id} not added to comparison")
        
        if self.verbose:
            logger.info(f"\n{'='*70}")
            logger.info(f"HEAD-TO-HEAD: {model1_id} vs {model2_id}")
            logger.info(f"{'='*70}")
        
        # Create table with two models
        config = GameConfig(
            num_players=2,
            starting_stack=self.config.starting_stack,
            small_blind=self.config.small_blind,
            big_blind=self.config.big_blind,
            verbose=False
        )
        
        players_models = [
            (self.models[model1_id], create_llm(model1_id)),
            (self.models[model2_id], create_llm(model2_id)),
        ]
        
        table = Table(config, players_models)
        results = table.run_session(num_hands=num_hands)
        
        # Extract final stacks from standings
        standings = results["standings"]
        model1_final = standings[0]["final_stack"] if standings[0]["name"] == self.models[model1_id] else standings[1]["final_stack"]
        model2_final = standings[1]["final_stack"] if standings[1]["name"] == self.models[model2_id] else standings[0]["final_stack"]
        
        if model1_final > model2_final:
            winner = model1_id
            loser = model2_id
        elif model2_final > model1_final:
            winner = model2_id
            loser = model1_id
        else:
            winner = None
        
        # Update stats
        match_result = {
            "timestamp": datetime.now().isoformat(),
            "model1": model1_id,
            "model2": model2_id,
            "num_hands": num_hands,
            "model1_final_stack": model1_final,
            "model2_final_stack": model2_final,
            "model1_profit": model1_final - self.config.starting_stack,
            "model2_profit": model2_final - self.config.starting_stack,
            "winner": winner,
            "results": results
        }
        
        # Update h2h records
        if winner:
            self.stats[winner].h2h_records[self.models[loser]]["wins"] += 1
            self.stats[loser].h2h_records[self.models[winner]]["losses"] += 1
        else:
            self.stats[model1_id].h2h_records[self.models[model2_id]]["ties"] += 1
            self.stats[model2_id].h2h_records[self.models[model1_id]]["ties"] += 1
        
        # Update overall stats
        for standing in results["standings"]:
            # Determine which model this standing belongs to
            if standing["name"] == self.models[model1_id]:
                model_id = model1_id
            else:
                model_id = model2_id
            
            stats = self.stats[model_id]
            stats.hands_played += num_hands
            stats.wins += standing["wins"]
            profit = standing["profit"]
            stats.total_profit += profit
            
            # Update stack depth stats
            final_stack = standing["final_stack"]
            if final_stack > stats.max_stack or stats.max_stack == 0:
                stats.max_stack = final_stack
            if final_stack < stats.min_stack or stats.min_stack == 0:
                stats.min_stack = final_stack
            
            if stats.hands_played > 0:
                stats.avg_stack = (stats.total_profit + self.config.starting_stack) / 1
        
        self.matches.append(match_result)
        
        if self.verbose:
            logger.info(f"\n{self.models[model1_id]} final stack: ${model1_final}")
            logger.info(f"{self.models[model2_id]} final stack: ${model2_final}")
            if winner:
                logger.info(f"\nWinner: {self.models[winner]}")
        
        return match_result
    
    def run_round_robin(self, num_hands_per_match: int = 10) -> Dict:
        """
        Run round-robin tournament where each model plays each other model.
        
        Args:
            num_hands_per_match: Hands per head-to-head match
            
        Returns:
            Round-robin results dictionary
        """
        model_ids = list(self.models.keys())
        
        if self.verbose:
            logger.info(f"\n{'='*70}")
            logger.info(f"ROUND-ROBIN TOURNAMENT")
            logger.info(f"Models: {', '.join([self.models[m] for m in model_ids])}")
            logger.info(f"Hands per match: {num_hands_per_match}")
            logger.info(f"{'='*70}")
        
        # Play each pairing
        for i, model1 in enumerate(model_ids):
            for model2 in model_ids[i+1:]:
                self.run_head_to_head(model1, model2, num_hands_per_match)
        
        if self.verbose:
            logger.info("\n" + "="*70)
            logger.info("ROUND-ROBIN COMPLETE")
            logger.info("="*70)
    
    def get_leaderboard(self) -> List[Tuple[str, ModelStats]]:
        """
        Get leaderboard sorted by win rate.
        
        Returns:
            List of (model_name, stats) tuples sorted by win rate (descending)
        """
        items = [(self.models[model_id], stats) 
                 for model_id, stats in self.stats.items()]
        return sorted(items, key=lambda x: x[1].win_rate, reverse=True)
    
    def print_leaderboard(self) -> None:
        """Print leaderboard to console."""
        leaderboard = self.get_leaderboard()
        
        print("\n" + "="*80)
        print("LEADERBOARD")
        print("="*80)
        print(f"{'Rank':<6} {'Model':<20} {'Wins':<8} {'Win Rate':<12} {'Profit':<12} {'ROI':<10}")
        print("-"*80)
        
        for rank, (model_name, stats) in enumerate(leaderboard, 1):
            print(f"{rank:<6} {model_name:<20} {stats.wins:<8} "
                  f"{stats.win_rate:>6.1f}%     "
                  f"${stats.total_profit:>8.2f}    "
                  f"{stats.roi:>6.1f}%")
        
        print("="*80 + "\n")
    
    def print_head_to_head(self) -> None:
        """Print head-to-head records."""
        print("\n" + "="*80)
        print("HEAD-TO-HEAD RECORDS")
        print("="*80)
        
        for model_id, stats in self.stats.items():
            if stats.h2h_records:
                print(f"\n{self.models[model_id]}:")
                for opponent, record in stats.h2h_records.items():
                    total = record["wins"] + record["losses"] + record["ties"]
                    print(f"  vs {opponent}: {record['wins']}-{record['losses']}-{record['ties']} "
                          f"({record['wins']}/{total})")
        
        print("="*80 + "\n")
    
    def export_results(self, filename: str) -> None:
        """
        Export comparison results to JSON.
        
        Args:
            filename: Output filename
        """
        results = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "models": self.models,
            "config": asdict(self.config),
            "matches": self.matches,
            "stats": {
                model_id: stats.to_dict() 
                for model_id, stats in self.stats.items()
            },
            "leaderboard": [
                {"rank": rank, "model": name, **stats.to_dict()}
                for rank, (name, stats) in enumerate(self.get_leaderboard(), 1)
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        if self.verbose:
            logger.info(f"Results exported to {filename}")
