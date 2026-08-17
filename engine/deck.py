import random
from typing import List, Tuple

class Deck:
    """Manages a standard 52-card poker deck."""
    
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SUITS = ['♠', '♥', '♦', '♣']
    
    def __init__(self):
        """Initialize a full deck of 52 cards."""
        self.cards: List[Tuple[str, str]] = []
        self.reset()
    
    def reset(self):
        """Reset the deck to all 52 cards and shuffle."""
        self.cards = [(rank, suit) for rank in self.RANKS for suit in self.SUITS]
        self.shuffle()
    
    def shuffle(self):
        """Randomly shuffle the deck."""
        random.shuffle(self.cards)
    
    def deal(self, num_cards: int = 1) -> List[Tuple[str, str]]:
        """
        Deal cards from the top of the deck.
        
        Args:
            num_cards: Number of cards to deal (default 1)
        
        Returns:
            List of (rank, suit) tuples
        
        Raises:
            ValueError: If not enough cards remain in deck
        """
        if num_cards > len(self.cards):
            raise ValueError(f"Not enough cards in deck. Requested {num_cards}, available {len(self.cards)}")
        
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt
    
    def remaining(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self.cards)
    
    def card_to_string(self, card: Tuple[str, str]) -> str:
        """Convert a card tuple to string representation (e.g., 'As', '2h')."""
        rank, suit = card
        suit_abbr = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
        return f"{rank}{suit_abbr[suit]}"
    
    def cards_to_string(self, cards: List[Tuple[str, str]]) -> str:
        """Convert a list of cards to a space-separated string."""
        return ' '.join(self.card_to_string(card) for card in cards)
