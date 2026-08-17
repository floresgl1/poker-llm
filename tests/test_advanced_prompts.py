#!/usr/bin/env python3
"""
Test enhanced strategic prompts.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.poker_state import GameState, Player
from llm_integration.prompt_builder import PromptBuilder


def test_enhanced_prompts():
    """Test the enhanced strategic prompt builder."""
    print("=" * 70)
    print("TESTING ENHANCED STRATEGIC PROMPTS")
    print("=" * 70)
    
    # Create a game scenario
    players = [
        Player(name="Alice", stack=1000, hand=[('A', '♠'), ('K', '♥')]),
        Player(name="Bob", stack=800, hand=[('Q', '♦'), ('J', '♣')]),
        Player(name="Charlie", stack=600, hand=[('9', '♠'), ('8', '♥')]),
    ]
    
    game = GameState(
        players=players,
        pot=150,
        bet_to_match=50,
        board=[('9', '♠'), ('8', '♦'), ('7', '♣')],
        to_act=0
    )
    
    # Set up position and contributions
    players[0].round_contribution = 50  # Alice matched the bet
    players[1].round_contribution = 30  # Bob behind
    players[2].round_contribution = 20  # Charlie behind
    
    # Create action history
    action_history = [
        {'hand': 1, 'street': 'preflop', 'player': 'Charlie', 'action': 'raise', 'amount': 20, 'pot': 30},
        {'hand': 1, 'street': 'preflop', 'player': 'Alice', 'action': 'call', 'amount': 20, 'pot': 50},
        {'hand': 1, 'street': 'preflop', 'player': 'Bob', 'action': 'raise', 'amount': 30, 'pot': 110},
        {'hand': 1, 'street': 'flop', 'player': 'Alice', 'action': 'call', 'amount': 30, 'pot': 150},
    ]
    
    # Build enhanced prompt for Alice
    print("\n" + "=" * 70)
    print("PROMPT FOR ALICE (Button, AK on 987 flop)")
    print("=" * 70 + "\n")
    
    prompt = PromptBuilder.build_player_prompt(game, players[0], action_history)
    print(prompt)
    
    # Test with different scenario: Bob's perspective
    print("\n" + "=" * 70)
    print("PROMPT FOR BOB (UTG+1, QJ on 987 flop)")
    print("=" * 70 + "\n")
    
    prompt_bob = PromptBuilder.build_player_prompt(game, players[1], action_history)
    print(prompt_bob)
    
    # Test with short stack scenario
    print("\n" + "=" * 70)
    print("PROMPT FOR CHARLIE (Short Stack 120 BBs)")
    print("=" * 70 + "\n")
    
    charlie_short = Player(name="Charlie", stack=120, hand=[('9', '♠'), ('8', '♥')])
    game.players[2] = charlie_short
    charlie_short.round_contribution = 20
    
    prompt_charlie = PromptBuilder.build_player_prompt(game, charlie_short, action_history)
    print(prompt_charlie)
    
    print("\n" + "=" * 70)
    print("ENHANCED PROMPTS TEST COMPLETE ✓")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_enhanced_prompts()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
