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
        if player.status != "active":
            return []  # folded or all-in players can't act
        
        actions = []
        remaining_chips = player.stack - player.round_contribution
        
        # Check if player can fold (only if there's a bet to match)
        if self.bet_to_match > player.round_contribution:
            actions.append("fold")
        
        # Check if player can check (no bet to match) or call (match the bet)
        if self.bet_to_match == player.round_contribution:
            actions.append("check")
        elif remaining_chips > 0:
            actions.append("call")
        
        # Can always bet/raise if they have chips left
        if remaining_chips > 0:
            actions.append("raise")
        
        return actions

    def view_for(self, player: Player) -> dict:
        """The filtered, per-seat view we'll hand to an LLM."""
        player_index = self.players.index(player)
        
        # Build view of other players (hide their hole cards)
        other_players = []
        for i, p in enumerate(self.players):
            if i == player_index:
                # This player sees their own hand
                other_players.append({
                    "name": p.name,
                    "stack": p.stack,
                    "hand": p.hand,
                    "status": p.status,
                    "round_contribution": p.round_contribution,
                    "position": i,
                })
            else:
                # Other players' hole cards are hidden
                other_players.append({
                    "name": p.name,
                    "stack": p.stack,
                    "hand": [None] * len(p.hand),  # hide hand
                    "status": p.status,
                    "round_contribution": p.round_contribution,
                    "position": i,
                })
        
        return {
            "players": other_players,
            "board": self.board,
            "pot": self.pot,
            "bet_to_match": self.bet_to_match,
            "to_act": self.to_act,
            "my_position": player_index,
            "legal_actions": self.legal_actions(player),
        }