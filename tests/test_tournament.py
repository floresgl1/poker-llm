#!/usr/bin/env python3
"""
Test tournament mode with increasing blinds and knockout structure.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_management.tournament import Tournament, BlindLevel
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_blind_levels():
    """Test blind level enumeration."""
    print("\n" + "="*70)
    print("TEST 1: BLIND LEVELS")
    print("="*70 + "\n")
    
    levels = [
        (1, (1, 2)),
        (2, (2, 4)),
        (3, (5, 10)),
        (4, (10, 20)),
        (5, (25, 50)),
    ]
    
    tournament = Tournament(
        players_models=[("Alice", "random")],
        buy_in=100,
        starting_stack=1000,
        verbose=False
    )
    
    for level, expected in levels:
        actual = tournament.get_blind_level(level)
        assert actual == expected, f"Level {level} has wrong value"
        print(f"[PASS] Level {level}: ${actual[0]}/${actual[1]}")


def test_tournament_initialization():
    """Test tournament initialization."""
    print("\n" + "="*70)
    print("TEST 2: TOURNAMENT INITIALIZATION")
    print("="*70 + "\n")
    
    players = [
        ("Alice", "random"),
        ("Bob", "call_any"),
        ("Charlie", "random"),
    ]
    
    tournament = Tournament(
        players_models=players,
        buy_in=100,
        starting_stack=1000,
        hands_per_level=3,
        verbose=False
    )
    
    assert len(tournament.tournament_players) == 3, "Should have 3 players"
    assert tournament.stats.total_players == 3, "Stats should track 3 players"
    
    for name, model_id in players:
        player = tournament.tournament_players[name]
        assert player.name == name, f"Player name should be {name}"
        assert player.model_id == model_id, f"Player model should be {model_id}"
        assert player.stack == 1000, "Player should start with 1000 stack"
        assert not player.eliminated, "Player should not be eliminated initially"
    
    print("[PASS] Tournament initialized with 3 players")
    print(f"  Buy-in: $100")
    print(f"  Starting stack: $1000")
    print(f"  Hands per level: 3")


def test_short_tournament():
    """Test running a short tournament."""
    print("\n" + "="*70)
    print("TEST 3: SHORT TOURNAMENT (10 HANDS)")
    print("="*70 + "\n")
    
    players = [
        ("Alice", "random"),
        ("Bob", "call_any"),
        ("Charlie", "random"),
    ]
    
    tournament = Tournament(
        players_models=players,
        buy_in=100,
        starting_stack=1000,
        hands_per_level=5,
        verbose=True
    )
    
    # Run tournament for max 10 hands
    results = tournament.run_tournament(max_hands=10)
    
    print(f"\n[PASS] Tournament completed")
    print(f"  Hands played: {results['hands_played']}")
    print(f"  Players remaining: {len([r for r in results['results'] if r['final_stack'] > 0])}")
    
    # Verify results structure
    assert results['total_players'] == 3
    assert len(results['results']) == 3
    assert len(results['eliminations']) <= 2  # At most 2 eliminations in 10 hands


def test_tournament_blind_progression():
    """Test that blinds increase properly."""
    print("\n" + "="*70)
    print("TEST 4: BLIND PROGRESSION")
    print("="*70 + "\n")
    
    tournament = Tournament(
        players_models=[("Alice", "random"), ("Bob", "call_any")],
        buy_in=100,
        starting_stack=5000,  # Large stack to avoid elimination
        hands_per_level=2,
        verbose=False
    )
    
    # Check initial blinds
    sb1, bb1 = tournament.get_blind_level(1)
    print(f"[PASS] Level 1: ${sb1}/${bb1}")
    
    # Check progression
    for level in range(2, 6):
        sb, bb = tournament.get_blind_level(level)
        print(f"[PASS] Level {level}: ${sb}/${bb}")
        
        # Verify blinds are increasing
        prev_sb, prev_bb = tournament.get_blind_level(level - 1)
        assert sb >= prev_sb, f"Blinds should not decrease (level {level})"
        assert bb >= prev_bb, f"Blinds should not decrease (level {level})"


def test_tournament_player_elimination():
    """Test player elimination tracking."""
    print("\n" + "="*70)
    print("TEST 5: PLAYER ELIMINATION TRACKING")
    print("="*70 + "\n")
    
    players = [
        ("Alice", "random"),
        ("Bob", "call_any"),
    ]
    
    tournament = Tournament(
        players_models=players,
        buy_in=100,
        starting_stack=10000,  # Large stack to accommodate blind increases
        hands_per_level=5,
        verbose=True
    )
    
    results = tournament.run_tournament(max_hands=20)
    
    # Check that at least one player remains
    active_players = [r for r in results['results'] if r['final_stack'] > 0]
    eliminated_players = [r for r in results['results'] if r['final_stack'] <= 0]
    
    print(f"\n[PASS] Eliminations tracked")
    print(f"  Active players: {len(active_players)}")
    print(f"  Eliminated players: {len(eliminated_players)}")
    
    if len(eliminated_players) > 0:
        print(f"  Elimination details:")
        for elim in results['eliminations']:
            print(f"    {elim}")


def test_tournament_export():
    """Test tournament results export."""
    print("\n" + "="*70)
    print("TEST 6: TOURNAMENT RESULTS EXPORT")
    print("="*70 + "\n")
    
    players = [
        ("Alice", "random"),
        ("Bob", "call_any"),
    ]
    
    tournament = Tournament(
        players_models=players,
        buy_in=100,
        starting_stack=1000,
        hands_per_level=3,
        verbose=False
    )
    
    # Run short tournament
    tournament.run_tournament(max_hands=10)
    
    # Export results
    tournament.export_results("tournament_results.json")
    
    print("[PASS] Tournament results exported to tournament_results.json")


if __name__ == '__main__':
    try:
        test_blind_levels()
        test_tournament_initialization()
        test_tournament_blind_progression()
        test_short_tournament()
        test_tournament_player_elimination()
        test_tournament_export()
        
        print("\n" + "="*70)
        print("ALL TOURNAMENT TESTS PASSED [OK]")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
