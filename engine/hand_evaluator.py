from typing import List, Tuple
from collections import Counter
from itertools import combinations

class HandEvaluator:
    """Evaluates poker hands and determines winners."""
    
    RANK_ORDER = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                  '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    # Hand rankings (higher is better)
    HAND_RANKINGS = {
        'high_card': 0,
        'pair': 1,
        'two_pair': 2,
        'three_of_a_kind': 3,
        'straight': 4,
        'flush': 5,
        'full_house': 6,
        'four_of_a_kind': 7,
        'straight_flush': 8,
        'royal_flush': 9,
    }
    
    @staticmethod
    def evaluate_hand(hole_cards: List[Tuple[str, str]], 
                     community_cards: List[Tuple[str, str]]) -> Tuple[int, str, List[int]]:
        """
        Evaluate the best 5-card hand from hole cards + community cards.
        
        Args:
            hole_cards: Player's 2 hole cards
            community_cards: 0-5 community cards (flop, turn, river)
        
        Returns:
            Tuple of (hand_rank_value, hand_name, kicker_ranks)
        """
        all_cards = hole_cards + community_cards
        
        # Get best 5-card combination
        best_hand = None
        best_rank = -1
        
        for five_cards in combinations(all_cards, 5):
            hand_rank, hand_name, kickers = HandEvaluator._evaluate_five_card_hand(list(five_cards))
            if hand_rank > best_rank:
                best_rank = hand_rank
                best_hand = (hand_rank, hand_name, kickers)
        
        return best_hand
    
    @staticmethod
    def _evaluate_five_card_hand(cards: List[Tuple[str, str]]) -> Tuple[int, str, List[int]]:
        """Evaluate a specific 5-card hand."""
        ranks = [HandEvaluator.RANK_ORDER[card[0]] for card in cards]
        suits = [card[1] for card in cards]
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        sorted_ranks = sorted(ranks)
        is_straight = (sorted_ranks[-1] - sorted_ranks[0] == 4) and len(set(sorted_ranks)) == 5
        
        # Special case: Ace-low straight (A-2-3-4-5)
        if sorted_ranks == [2, 3, 4, 5, 14]:
            is_straight = True
            kickers = [5, 4, 3, 2, 1]  # Treat ace as 1 in this case
        else:
            kickers = sorted(ranks, reverse=True)
        
        # Count ranks
        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        # Determine hand type
        if is_straight and is_flush:
            if sorted_ranks == [10, 11, 12, 13, 14]:
                hand_name = 'royal_flush'
                rank = HandEvaluator.HAND_RANKINGS['royal_flush']
            else:
                hand_name = 'straight_flush'
                rank = HandEvaluator.HAND_RANKINGS['straight_flush']
        elif counts[0][1] == 4:
            hand_name = 'four_of_a_kind'
            rank = HandEvaluator.HAND_RANKINGS['four_of_a_kind']
            kickers = [counts[0][0], counts[1][0]]
        elif counts[0][1] == 3 and counts[1][1] == 2:
            hand_name = 'full_house'
            rank = HandEvaluator.HAND_RANKINGS['full_house']
            kickers = [counts[0][0], counts[1][0]]
        elif is_flush:
            hand_name = 'flush'
            rank = HandEvaluator.HAND_RANKINGS['flush']
        elif is_straight:
            hand_name = 'straight'
            rank = HandEvaluator.HAND_RANKINGS['straight']
        elif counts[0][1] == 3:
            hand_name = 'three_of_a_kind'
            rank = HandEvaluator.HAND_RANKINGS['three_of_a_kind']
            kickers = [counts[0][0], counts[1][0], counts[2][0]]
        elif counts[0][1] == 2 and counts[1][1] == 2:
            hand_name = 'two_pair'
            rank = HandEvaluator.HAND_RANKINGS['two_pair']
            kickers = [max(counts[0][0], counts[1][0]), min(counts[0][0], counts[1][0]), counts[2][0]]
        elif counts[0][1] == 2:
            hand_name = 'pair'
            rank = HandEvaluator.HAND_RANKINGS['pair']
            kickers = [counts[0][0]] + sorted([counts[i][0] for i in range(1, 4)], reverse=True)
        else:
            hand_name = 'high_card'
            rank = HandEvaluator.HAND_RANKINGS['high_card']
        
        return (rank, hand_name, kickers)
    
    @staticmethod
    def compare_hands(player1_hand: Tuple[int, str, List[int]], 
                     player2_hand: Tuple[int, str, List[int]]) -> int:
        """
        Compare two evaluated hands.
        
        Returns:
            1 if player1 wins
            -1 if player2 wins
            0 if tie
        """
        rank1, name1, kickers1 = player1_hand
        rank2, name2, kickers2 = player2_hand
        
        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        else:
            # Same hand ranking, compare kickers
            for k1, k2 in zip(kickers1, kickers2):
                if k1 > k2:
                    return 1
                elif k1 < k2:
                    return -1
            return 0  # Exact tie
    
    @staticmethod
    def find_winner(players_hands: List[Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]],
                   community_cards: List[Tuple[str, str]]) -> int:
        """
        Determine the winner among multiple players.
        
        Args:
            players_hands: List of (player_index, hole_cards) tuples
            community_cards: Shared community cards
        
        Returns:
            Index of the winning player
        """
        evaluated_hands = []
        for idx, (hole_cards, _) in enumerate(players_hands):
            hand = HandEvaluator.evaluate_hand(hole_cards, community_cards)
            evaluated_hands.append((idx, hand))
        
        winner_idx = 0
        for idx, hand in evaluated_hands[1:]:
            if HandEvaluator.compare_hands(hand, evaluated_hands[winner_idx][1]) > 0:
                winner_idx = evaluated_hands.index((idx, hand))
        
        return evaluated_hands[winner_idx][0]
