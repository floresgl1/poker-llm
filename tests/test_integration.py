#!/usr/bin/env python3
"""
Integration test: Run a complete poker session with LLM players.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from game_management.game_config import GameConfig
from game_management.table import Table
from llm_integration.llm_models import create_llm


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_single_hand():
    """Test a single hand with random players."""
    print("\n" + "="*60)
    print("TEST 1: SINGLE HAND")
    print("="*60 + "\n")
    
    # Create config
    config = GameConfig(
        num_players=3,
        starting_stack=500,
        small_blind=5,
        big_blind=10,
        verbose=True
    )
    
    # Create LLM players (using random for testing)
    players_models = [
        ("Alice", create_llm("random")),
        ("Bob", create_llm("random")),
        ("Charlie", create_llm("random")),
    ]
    
    # Create table and run hand
    table = Table(config, players_models)
    winner = table.run_single_hand()
    
    print(f"\n[PASS] Hand complete. Winner: {winner}")
    print("\nFinal stacks:")
    for player in table.game_runner.players:
        print(f"  {player.name}: ${player.stack}")


def test_short_session():
    """Test a 5-hand session."""
    print("\n" + "="*60)
    print("TEST 2: 5-HAND SESSION")
    print("="*60 + "\n")
    
    # Create config
    config = GameConfig(
        num_players=2,
        starting_stack=200,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    # Create LLM players
    players_models = [
        ("Alice", create_llm("random")),
        ("Bob", create_llm("call_any")),
    ]
    
    # Create table and run session
    table = Table(config, players_models)
    results = table.run_session(num_hands=5)
    
    print("\n[PASS] Session complete!")
    table.print_results()


def test_three_player_session():
    """Test 3-player session with different strategies."""
    print("\n" + "="*60)
    print("TEST 3: 3-PLAYER MIXED STRATEGIES")
    print("="*60 + "\n")
    
    # Create config
    config = GameConfig(
        num_players=3,
        starting_stack=300,
        small_blind=5,
        big_blind=10,
        verbose=False
    )
    
    # Create LLM players with different strategies
    players_models = [
        ("Alice", create_llm("random")),       # Random moves
        ("Bob", create_llm("call_any")),       # Always calls
        ("Charlie", create_llm("random")),     # Random moves
    ]
    
    # Create table and run session
    table = Table(config, players_models)
    results = table.run_session(num_hands=10)
    
    print("\n[PASS] Session complete!")
    table.print_results()
    
    # Export results
    export_file = "session_results.json"
    table.export_hand_history(export_file)
    print(f"[PASS] Results saved to {export_file}")


if __name__ == '__main__':
    setup_logging()
    
    try:
        test_single_hand()
        test_short_session()
        test_three_player_session()
        
        print("\n" + "="*60)
        print("ALL INTEGRATION TESTS PASSED [OK]")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
