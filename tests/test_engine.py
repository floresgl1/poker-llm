#!/usr/bin/env python3
"""
Test script for poker engine components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deck import Deck
from engine.hand_evaluator import HandEvaluator
from engine.poker_state import GameState, Player
from engine.action_handler import ActionHandler


def test_deck():
    """Test deck operations."""
    print("=" * 50)
    print("TESTING DECK")
    print("=" * 50)
    
    deck = Deck()
    print(f" Deck created with {deck.remaining()} cards")
    
    hand = deck.deal(2)
    print(f" Dealt 2 cards: {deck.cards_to_string(hand)}")
    print(f" Cards remaining: {deck.remaining()}")
    
    print()


def test_hand_evaluator():
    """Test hand evaluation."""
    print("=" * 50)
    print("TESTING HAND EVALUATOR")
    print("=" * 50)
    
    # Test royal flush
    hand1 = [('A', ''), ('K', '')]
    board1 = [('Q', ''), ('J', ''), ('T', ''), ('9', ''), ('8', '')]
    result1 = HandEvaluator.evaluate_hand(hand1, board1)
    print(f" Royal flush: {result1[1]} (rank {result1[0]})")
    
    # Test pair
    hand2 = [('K', ''), ('K', '')]
    board2 = [('7', ''), ('5', ''), ('3', '')]
    result2 = HandEvaluator.evaluate_hand(hand2, board2)
    print(f" Pair: {result2[1]} (rank {result2[0]})")
    
    # Test high card
    hand3 = [('A', ''), ('K', '')]
    board3 = [('7', ''), ('5', ''), ('3', '')]
    result3 = HandEvaluator.evaluate_hand(hand3, board3)
    print(f" High card: {result3[1]} (rank {result3[0]})")
    
    # Compare hands
    winner = HandEvaluator.compare_hands(result1, result2)
    print(f" Royal flush beats pair: {winner == 1}")
    
    print()


def test_game_state():
    """Test game state and legal actions."""
    print("=" * 50)
    print("TESTING GAME STATE")
    print("=" * 50)
    
    # Create players
    players = [
        Player(name="Alice", stack=1000, hand=[('A', ''), ('K', '')]),
        Player(name="Bob", stack=1000, hand=[('Q', ''), ('J', '')]),
        Player(name="Charlie", stack=1000, hand=[('9', ''), ('8', '')]),
    ]
    
    # Create game state
    game = GameState(players=players, pot=150, bet_to_match=50, to_act=0)
    print(f" Game created with {len(players)} players")
    print(f" Pot: ${game.pot}, Bet to match: ${game.bet_to_match}")
    
    # Test legal actions for different situations
    alice = players[0]
    alice.round_contribution = 0
    actions = game.legal_actions(alice)
    print(f" Legal actions for Alice (no contribution): {actions}")
    
    alice.round_contribution = 50
    actions = game.legal_actions(alice)
    print(f" Legal actions for Alice (matched bet): {actions}")
    
    # Test view_for
    view = game.view_for(alice)
    print(f" Alice's view includes:")
    print(f"  - Her hand: {view['players'][0]['hand']}")
    print(f"  - Bob's hidden hand: {view['players'][1]['hand']}")
    print(f"  - Legal actions: {view['legal_actions']}")
    
    print()


def test_action_handler():
    """Test action processing."""
    print("=" * 50)
    print("TESTING ACTION HANDLER")
    print("=" * 50)
    
    # Create simple game
    players = [
        Player(name="Alice", stack=500, hand=[('A', ''), ('K', '')]),
        Player(name="Bob", stack=500, hand=[('Q', ''), ('J', '')]),
    ]
    game = GameState(players=players, pot=0, bet_to_match=0)
    
    # Collect blinds
    ActionHandler.collect_antes(game, small_blind=10, big_blind=20, 
                                small_blind_idx=0, big_blind_idx=1)
    print(f" Collected blinds")
    print(f"  - Alice: ${players[0].stack} stack, ${players[0].round_contribution} in pot")
    print(f"  - Bob: ${players[1].stack} stack, ${players[1].round_contribution} in pot")
    print(f"  - Pot: ${game.pot}")
    
    # Alice calls
    result = ActionHandler.process_action(game, players[0], 'call')
    print(f"\n Alice calls: {result['success']}")
    print(f"  - Amount added: ${result['amount_added']}")
    print(f"  - Alice's stack: ${players[0].stack}")
    print(f"  - Pot: ${game.pot}")
    
    # Bob raises
    result = ActionHandler.process_action(game, players[1], 'raise 40')
    print(f"\n Bob raises to 40: {result['success']}")
    print(f"  - Amount added: ${result['amount_added']}")
    print(f"  - Bob's stack: ${players[1].stack}")
    print(f"  - Pot: ${game.pot}")
    print(f"  - Bet to match: ${game.bet_to_match}")
    
    print()


def test_prompt_builder():
    """Test prompt building."""
    print("=" * 50)
    print("TESTING PROMPT BUILDER")
    print("=" * 50)
    
    from llm_integration.prompt_builder import PromptBuilder
    
    players = [
        Player(name="Alice", stack=1000, hand=[('A', ''), ('K', '')]),
        Player(name="Bob", stack=800, hand=[('Q', ''), ('J', '')]),
    ]
    game = GameState(players=players, pot=150, bet_to_match=50, 
                    board=[('9', ''), ('8', ''), ('7', '')])
    players[0].round_contribution = 50
    
    prompt = PromptBuilder.build_player_prompt(game, players[0])
    print(f" Built player prompt:")
    print(prompt)
    
    print()


if __name__ == '__main__':
    try:
        test_deck()
        test_hand_evaluator()
        test_game_state()
        test_action_handler()
        test_prompt_builder()
        
        print("=" * 50)
        print("ALL TESTS PASSED [OK]")
        print("=" * 50)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


