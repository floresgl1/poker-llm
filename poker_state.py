from dataclasses import dataclass, field

@dataclass
class Player:
    name: str          # also the model id, e.g. "claude" / "gpt-4o"
    stack: int
    hand: list = field(default_factory=list)   # list of (rank, suit) tuples
    status: str = "active"                       # active | folded | all-in
    round_contribution: int = 0                  # chips put in THIS betting round

@dataclass
class GameState:
    players: list                     # list[Player], seated in order
    board: list = field(default_factory=list)    # community cards
    pot: int = 0
    bet_to_match: int = 0             # highest round_contribution this round
    to_act: int = 0                  # index into players — whose turn
    last_aggressor: int = 0          # index of last player to bet/raise

    def legal_actions(self, player: Player) -> list[str]:
        """What can THIS player legally do right now?"""
        # TODO: your logic here
        ...

    def view_for(self, player: Player) -> dict:
        """The filtered, per-seat view we'll hand to an LLM."""
        # TODO: return only what this player is allowed to see
        ...