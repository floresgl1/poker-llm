from typing import Dict, Tuple, List, Optional
from engine.poker_state import GameState, Player


class ActionHandler:
    """Processes player actions and updates game state."""
    
    @staticmethod
    def process_action(game_state: GameState, player: Player, action: str, 
                      bet_amount: int = 0) -> Dict:
        """
        Process a player action and update game state.
        
        Args:
            game_state: Current game state
            player: Player taking action
            action: Action type ('fold', 'check', 'call', 'raise')
            bet_amount: Amount to bet/raise (only used for raise)
        
        Returns:
            Dict with action result and updates
        """
        result = {
            'success': False,
            'action': action,
            'player': player.name,
            'amount_added': 0,
            'error': None
        }
        
        # Validate action is legal
        legal_actions = game_state.legal_actions(player)
        action_type = action.split()[0].lower() if action else ''
        
        if action_type not in legal_actions:
            result['error'] = f"Illegal action: {action}. Legal actions: {legal_actions}"
            return result
        
        # Process based on action type
        if action_type == 'fold':
            return ActionHandler._handle_fold(game_state, player, result)
        elif action_type == 'check':
            return ActionHandler._handle_check(game_state, player, result)
        elif action_type == 'call':
            return ActionHandler._handle_call(game_state, player, result)
        elif action_type == 'raise':
            return ActionHandler._handle_raise(game_state, player, action, bet_amount, result)
        else:
            result['error'] = f"Unknown action: {action}"
            return result
    
    @staticmethod
    def _handle_fold(game_state: GameState, player: Player, result: Dict) -> Dict:
        """Handle fold action."""
        player.status = 'folded'
        result['success'] = True
        result['amount_added'] = 0
        return result
    
    @staticmethod
    def _handle_check(game_state: GameState, player: Player, result: Dict) -> Dict:
        """Handle check action."""
        # Check is only valid if no bet to match
        if game_state.bet_to_match > player.round_contribution:
            result['error'] = "Cannot check when there's a bet to match"
            return result
        
        result['success'] = True
        result['amount_added'] = 0
        return result
    
    @staticmethod
    def _handle_call(game_state: GameState, player: Player, result: Dict) -> Dict:
        """Handle call action."""
        amount_to_call = game_state.bet_to_match - player.round_contribution
        
        if amount_to_call > player.stack:
            # All-in
            amount_to_call = player.stack
            player.status = 'all-in'
        
        player.stack -= amount_to_call
        player.round_contribution += amount_to_call
        game_state.pot += amount_to_call
        
        result['success'] = True
        result['amount_added'] = amount_to_call
        return result
    
    @staticmethod
    def _handle_raise(game_state: GameState, player: Player, action: str, 
                     bet_amount: int, result: Dict) -> Dict:
        """Handle raise action."""
        # Parse bet amount from action if not provided
        if bet_amount == 0:
            parts = action.split()
            if len(parts) > 1:
                try:
                    bet_amount = int(parts[1])
                except ValueError:
                    result['error'] = "Invalid raise amount"
                    return result
        
        # Calculate total amount to put in (call + raise)
        to_call = game_state.bet_to_match - player.round_contribution
        total_bet = to_call + bet_amount
        
        if total_bet > player.stack:
            # All-in
            total_bet = player.stack
            player.status = 'all-in'
        
        player.stack -= total_bet
        player.round_contribution += total_bet
        game_state.pot += total_bet
        
        # Update bet to match for other players
        game_state.bet_to_match = player.round_contribution
        game_state.last_aggressor = game_state.players.index(player)
        
        result['success'] = True
        result['amount_added'] = total_bet
        return result
    
    @staticmethod
    def move_to_next_player(game_state: GameState) -> Optional[int]:
        """
        Move to the next active player who needs to act.
        
        Returns:
            Index of next player, or None if round complete
        """
        num_players = len(game_state.players)
        current = game_state.to_act
        
        for _ in range(num_players):
            current = (current + 1) % num_players
            player = game_state.players[current]
            
            # Skip folded players
            if player.status != 'folded':
                game_state.to_act = current
                return current
        
        return None  # All other players folded
    
    @staticmethod
    def is_betting_round_complete(game_state: GameState) -> bool:
        """
        Check if all active players have acted and matched the current bet.
        
        Returns:
            True if round is complete, False otherwise
        """
        active_players = [p for p in game_state.players if p.status in ['active', 'all-in']]
        
        if not active_players:
            return True
        
        # All active players must have matched the bet
        for player in active_players:
            if player.status == 'active' and player.round_contribution < game_state.bet_to_match:
                return False
        
        return True
    
    @staticmethod
    def reset_round_for_next_street(game_state: GameState):
        """
        Reset per-round tracking for next betting street (flop, turn, river).
        """
        game_state.bet_to_match = 0
        for player in game_state.players:
            if player.status != 'folded':
                player.round_contribution = 0
        game_state.to_act = ActionHandler._find_first_to_act(game_state)
    
    @staticmethod
    def _find_first_to_act(game_state: GameState) -> int:
        """Find the first active player to act (typically small blind position)."""
        for i, player in enumerate(game_state.players):
            if player.status != 'folded':
                return i
        return 0
    
    @staticmethod
    def collect_antes(game_state: GameState, small_blind: int, big_blind: int, 
                     small_blind_idx: int, big_blind_idx: int):
        """
        Collect blinds at the start of a hand.
        
        Args:
            game_state: Current game state
            small_blind: Small blind amount
            big_blind: Big blind amount
            small_blind_idx: Index of small blind player
            big_blind_idx: Index of big blind player
        """
        sb_player = game_state.players[small_blind_idx]
        bb_player = game_state.players[big_blind_idx]
        
        # Collect small blind
        sb_amount = min(small_blind, sb_player.stack)
        sb_player.stack -= sb_amount
        sb_player.round_contribution = sb_amount
        game_state.pot += sb_amount
        
        # Collect big blind
        bb_amount = min(big_blind, bb_player.stack)
        bb_player.stack -= bb_amount
        bb_player.round_contribution = bb_amount
        game_state.pot += bb_amount
        
        game_state.bet_to_match = bb_amount
    
    @staticmethod
    def get_active_players(game_state: GameState) -> List[Player]:
        """Get list of players who haven't folded."""
        return [p for p in game_state.players if p.status != 'folded']
    
    @staticmethod
    def count_all_in_players(game_state: GameState) -> int:
        """Count players who are all-in."""
        return sum(1 for p in game_state.players if p.status == 'all-in')
