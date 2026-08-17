#!/usr/bin/env python3
"""
Comprehensive example demonstrating Model Comparison and Tournament Mode.
Shows how to use both features together for complete LLM evaluation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_management.game_config import GameConfig
from game_management.model_comparison import ModelComparison
from game_management.tournament import Tournament
import logging

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress detailed logs for cleaner output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def demo_model_comparison():
    """Demonstrate model comparison framework."""
    print("\n" + "="*80)
    print("DEMO 1: MODEL COMPARISON (HEAD-TO-HEAD)")
    print("="*80 + "\n")
    
    config = GameConfig(
        num_players=2,
        starting_stack=500,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    comparison = ModelComparison(config, verbose=False)
    comparison.add_model("random", "Random Strategy")
    comparison.add_model("call_any", "Call-Any Strategy")
    
    print("Running 15-hand match: Random vs Call-Any\n")
    result = comparison.run_head_to_head("random", "call_any", num_hands=15)
    
    print(f"Results:")
    print(f"  Random final stack: ${result['model1_final_stack']}")
    print(f"  Call-Any final stack: ${result['model2_final_stack']}")
    if result['winner']:
        print(f"  Winner: {result['winner']}")
    print(f"  Profit swing: ${abs(result['model1_profit'] - result['model2_profit']):.0f}")
    
    comparison.export_results("demo_comparison.json")
    print("\nResults exported to demo_comparison.json")


def demo_tournament():
    """Demonstrate tournament mode."""
    print("\n" + "="*80)
    print("DEMO 2: TOURNAMENT MODE (INCREASING BLINDS)")
    print("="*80 + "\n")
    
    players = [
        ("Alice", "random"),
        ("Bob", "call_any"),
        ("Charlie", "random"),
    ]
    
    print(f"Tournament Details:")
    print(f"  Players: {len(players)}")
    print(f"  Starting stack: $5000")
    print(f"  Hands per level: 3")
    print(f"  Max 20 hands\n")
    
    tournament = Tournament(
        players_models=players,
        buy_in=100,
        starting_stack=5000,  # Larger to accommodate blind levels
        hands_per_level=3,
        verbose=False
    )
    
    results = tournament.run_tournament(max_hands=20)
    
    print(f"Tournament Results:")
    print(f"  Hands played: {results['hands_played']}")
    print(f"  Final results:")
    for result in results['results']:
        print(f"    {result['finish_position']}. {result['player_name']:12} "
              f"${result['final_stack']:6} ({result['profit_loss']:+6})")
    
    tournament.export_results("demo_tournament.json")
    print("\nResults exported to demo_tournament.json")


def demo_advanced_comparison():
    """Demonstrate advanced model comparison with round-robin."""
    print("\n" + "="*80)
    print("DEMO 3: ADVANCED COMPARISON (ROUND-ROBIN)")
    print("="*80 + "\n")
    
    config = GameConfig(
        num_players=2,
        starting_stack=300,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    comparison = ModelComparison(config, verbose=False)
    comparison.add_model("random", "Random")
    comparison.add_model("call_any", "Call-Any")
    
    print("Running round-robin: Each model plays each other (10 hands per match)\n")
    comparison.run_round_robin(num_hands_per_match=10)
    
    print("Leaderboard:")
    leaderboard = comparison.get_leaderboard()
    for rank, (name, stats) in enumerate(leaderboard, 1):
        print(f"  {rank}. {name:20} Win Rate: {stats.win_rate:6.1f}% "
              f"Profit: ${stats.total_profit:8.2f}")
    
    print("\nHead-to-Head Records:")
    for model_id, stats in comparison.stats.items():
        if stats.h2h_records:
            print(f"  {comparison.models[model_id]}:")
            for opponent, record in stats.h2h_records.items():
                total = record['wins'] + record['losses'] + record['ties']
                print(f"    vs {opponent}: {record['wins']}/{total}")
    
    comparison.export_results("demo_round_robin.json")
    print("\nResults exported to demo_round_robin.json")


def main():
    """Run all demonstrations."""
    print("\n" + "="*80)
    print("POKER LLM ENGINE - COMPREHENSIVE DEMONSTRATION")
    print("Showcasing Model Comparison and Tournament Mode")
    print("="*80)
    
    try:
        demo_model_comparison()
        demo_tournament()
        demo_advanced_comparison()
        
        print("\n" + "="*80)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("Check demo_comparison.json, demo_tournament.json, and")
        print("demo_round_robin.json for detailed results.")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
