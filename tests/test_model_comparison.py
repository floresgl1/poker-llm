#!/usr/bin/env python3
"""
Test model comparison framework.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_management.game_config import GameConfig
from game_management.model_comparison import ModelComparison
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_head_to_head():
    """Test head-to-head comparison between two models."""
    print("\n" + "="*70)
    print("TEST 1: HEAD-TO-HEAD COMPARISON")
    print("="*70 + "\n")
    
    # Create config
    config = GameConfig(
        num_players=2,
        starting_stack=300,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    # Create comparison
    comparison = ModelComparison(config, verbose=True)
    comparison.add_model("random", "Random Strategy")
    comparison.add_model("call_any", "Call Any Strategy")
    
    # Run head-to-head
    result = comparison.run_head_to_head("random", "call_any", num_hands=10)
    
    print(f"\n[PASS] Head-to-head complete")
    print(f"  Random final stack: ${result['model1_final_stack']}")
    print(f"  Call Any final stack: ${result['model2_final_stack']}")
    if result['winner']:
        print(f"  Winner: {result['winner']}")


def test_round_robin():
    """Test round-robin tournament between multiple models."""
    print("\n" + "="*70)
    print("TEST 2: ROUND-ROBIN TOURNAMENT")
    print("="*70 + "\n")
    
    # Create config
    config = GameConfig(
        num_players=2,
        starting_stack=300,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    # Create comparison with 3 models
    comparison = ModelComparison(config, verbose=True)
    comparison.add_model("random", "Random")
    comparison.add_model("call_any", "Call Any")
    # Note: Could add more models here if they exist
    
    # Run round-robin (each model plays each other)
    comparison.run_round_robin(num_hands_per_match=5)
    
    # Print results
    comparison.print_leaderboard()
    comparison.print_head_to_head()
    
    # Export results
    comparison.export_results("comparison_results.json")
    print("[PASS] Round-robin complete, results exported")


def test_statistics_tracking():
    """Test that statistics are tracked correctly."""
    print("\n" + "="*70)
    print("TEST 3: STATISTICS TRACKING")
    print("="*70 + "\n")
    
    # Create config
    config = GameConfig(
        num_players=2,
        starting_stack=300,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    # Create comparison
    comparison = ModelComparison(config, verbose=False)
    comparison.add_model("random", "Random")
    comparison.add_model("call_any", "Call Any")
    
    # Run match
    comparison.run_head_to_head("random", "call_any", num_hands=5)
    
    # Verify stats
    random_stats = comparison.stats["random"]
    call_any_stats = comparison.stats["call_any"]
    
    assert random_stats.hands_played > 0, "Random player should have played hands"
    assert call_any_stats.hands_played > 0, "Call Any player should have played hands"
    
    print(f"[PASS] Statistics tracked correctly")
    print(f"  Random: {random_stats.hands_played} hands, {random_stats.wins} wins, "
          f"win rate: {random_stats.win_rate:.1f}%, profit: ${random_stats.total_profit:.2f}")
    print(f"  Call Any: {call_any_stats.hands_played} hands, {call_any_stats.wins} wins, "
          f"win rate: {call_any_stats.win_rate:.1f}%, profit: ${call_any_stats.total_profit:.2f}")


if __name__ == '__main__':
    try:
        test_head_to_head()
        test_round_robin()
        test_statistics_tracking()
        
        print("\n" + "="*70)
        print("ALL MODEL COMPARISON TESTS PASSED [OK]")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
