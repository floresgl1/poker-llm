from dataclasses import dataclass


@dataclass
class GameConfig:
    """Configuration for poker game sessions."""
    
    # Game structure
    num_players: int = 2
    starting_stack: int = 1000
    small_blind: int = 10
    big_blind: int = 20
    
    # Betting
    min_bet: int = 10
    max_raise: int = None  # None = unlimited (no-limit), or set a cap
    allow_all_in: bool = True
    
    # Game flow
    max_hands: int = None  # None = unlimited
    auto_play: bool = False  # Whether to auto-skip decision delays
    
    # Logging
    log_all_actions: bool = True
    verbose: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if self.num_players < 2:
            raise ValueError("Need at least 2 players")
        if self.small_blind <= 0 or self.big_blind <= 0:
            raise ValueError("Blinds must be positive")
        if self.big_blind != self.small_blind * 2:
            raise ValueError("Big blind should be 2x small blind")
        if self.starting_stack < self.big_blind * 10:
            raise ValueError("Starting stack should be at least 10x big blind")
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            'num_players': self.num_players,
            'starting_stack': self.starting_stack,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'min_bet': self.min_bet,
            'max_raise': self.max_raise,
            'allow_all_in': self.allow_all_in,
            'max_hands': self.max_hands,
        }
    
    @staticmethod
    def micro_stakes() -> 'GameConfig':
        """Micro stakes config (0.01/0.02)."""
        return GameConfig(
            num_players=6,
            starting_stack=500,
            small_blind=1,
            big_blind=2
        )
    
    @staticmethod
    def cash_game() -> 'GameConfig':
        """Cash game config (0.10/0.20)."""
        return GameConfig(
            num_players=6,
            starting_stack=2000,
            small_blind=10,
            big_blind=20
        )
    
    @staticmethod
    def tournament_style() -> 'GameConfig':
        """Tournament config with increasing blinds."""
        return GameConfig(
            num_players=6,
            starting_stack=1500,
            small_blind=25,
            big_blind=50
        )
    
    @staticmethod
    def heads_up() -> 'GameConfig':
        """Heads-up (1v1) config."""
        return GameConfig(
            num_players=2,
            starting_stack=1000,
            small_blind=5,
            big_blind=10
        )
