from typing import Dict, List, Tuple, Optional
from enum import Enum
from engine.poker_state import GameState, Player


class Position(Enum):
    """Poker positions at the table."""
    BUTTON = "Button (best position)"
    CUTOFF = "Cutoff (strong position)"
    UTG_PLUS_1 = "UTG+1 (weak position)"
    UTG = "UTG (worst position)"
    SMALL_BLIND = "Small Blind"
    BIG_BLIND = "Big Blind"


class StackDepth(Enum):
    """Stack depth categories."""
    SHORT = "short-stack (<20 BBs)"
    MEDIUM = "medium-stack (20-100 BBs)"
    DEEP = "deep-stack (>100 BBs)"


class PromptBuilder:
    """Builds strategic prompts for LLMs from game state."""
    
    @staticmethod
    def build_player_prompt(game_state: GameState, player: Player, 
                           action_history: List[Dict] = None) -> str:
        """
        Build an advanced strategic poker decision prompt for an LLM.
        
        Args:
            game_state: Current game state
            player: Player to build prompt for
            action_history: Optional list of recent actions
        
        Returns:
            Formatted prompt string with strategic analysis
        """
        view = game_state.view_for(player)
        legal_actions = view['legal_actions']
        
        # Calculate strategic metrics
        my_position = PromptBuilder._get_position(game_state, view['my_position'])
        my_stack_depth = PromptBuilder._get_stack_depth(player.stack, game_state)
        pot_odds = PromptBuilder._calculate_pot_odds(game_state, player)
        opponent_stats = PromptBuilder._analyze_opponents(game_state, view, action_history)
        
        prompt = "=== STRATEGIC POKER DECISION ===\n\n"
        
        # Position information
        prompt += f"YOUR POSITION: {my_position.value}\n"
        prompt += f"TABLE SIZE: {len(game_state.players)} players\n"
        prompt += f"STACK DEPTH: {my_stack_depth.value}\n\n"
        
        # Your hand and situation
        hand_str = PromptBuilder._cards_to_string(player.hand)
        prompt += f"YOUR HAND: {hand_str}\n"
        prompt += f"YOUR STACK: ${player.stack}\n"
        prompt += f"YOUR CONTRIBUTION THIS ROUND: ${player.round_contribution}\n\n"
        
        # Board information
        if game_state.board:
            board_str = PromptBuilder._cards_to_string(game_state.board)
            prompt += f"COMMUNITY CARDS: {board_str} ({len(game_state.board)} cards)\n"
        else:
            prompt += "COMMUNITY CARDS: (Preflop - no cards yet)\n"
        
        # Pot information with odds
        prompt += f"\nPOT SIZE: ${game_state.pot}\n"
        prompt += f"BET TO MATCH: ${game_state.bet_to_match}\n"
        if pot_odds:
            prompt += f"POT ODDS: {pot_odds['ratio']:.1f}:1 (need {pot_odds['equity']:.1f}% equity to break even)\n"
        prompt += f"\n"
        
        # Opponent information with tendencies
        prompt += "OPPONENTS & TENDENCIES:\n"
        for i, opp in enumerate(view['players']):
            if i != view['my_position']:
                stack_depth = PromptBuilder._get_stack_depth(opp['stack'], game_state)
                prompt += f"  {opp['name']}:\n"
                prompt += f"    - Stack: ${opp['stack']} ({stack_depth.value})\n"
                prompt += f"    - Contribution: ${opp['round_contribution']}\n"
                prompt += f"    - Status: {opp['status']}\n"
                
                if opp['name'] in opponent_stats:
                    stats = opponent_stats[opp['name']]
                    prompt += f"    - Aggression: {stats['aggression']}\n"
                    prompt += f"    - Fold rate: {stats['fold_rate']}\n"
                prompt += "\n"
        
        # Recent action history with analysis
        if action_history:
            recent_streets = {}
            for action in action_history[-10:]:
                street = action.get('street', 'unknown')
                if street not in recent_streets:
                    recent_streets[street] = []
                recent_streets[street].append(action)
            
            prompt += "RECENT ACTION SEQUENCE:\n"
            for street, actions in recent_streets.items():
                prompt += f"  {street.upper()}:\n"
                for action in actions:
                    prompt += f"    - {action['player']}: {action['action']}\n"
            prompt += "\n"
        
        # Strategic considerations
        prompt += "STRATEGIC CONSIDERATIONS:\n"
        prompt += PromptBuilder._get_strategic_advice(
            game_state, player, my_position, my_stack_depth, legal_actions
        )
        prompt += "\n"
        
        # Legal actions
        prompt += f"LEGAL ACTIONS: {', '.join(legal_actions)}\n\n"
        
        # Decision request
        prompt += "Make your decision based on:\n"
        prompt += "1. Pot odds and expected value\n"
        prompt += "2. Your position at the table\n"
        prompt += "3. Stack sizes (yours and opponents')\n"
        prompt += "4. Recent opponent actions and tendencies\n"
        prompt += "5. Board texture and hand strength\n\n"
        prompt += "What is your action? Respond with ONLY one legal action.\n"
        
        return prompt
    
    @staticmethod
    def build_initial_prompt(game_state: GameState, player: Player,
                            small_blind: int, big_blind: int) -> str:
        """
        Build initial prompt when player first joins/game starts.
        
        Args:
            game_state: Current game state
            player: Player
            small_blind: Small blind amount
            big_blind: Big blind amount
        
        Returns:
            Formatted prompt string
        """
        prompt = "=== NEW POKER GAME ===\n\n"
        prompt += f"You are playing as: {player.name}\n"
        prompt += f"Your starting stack: ${player.stack}\n"
        prompt += f"Small blind: ${small_blind}\n"
        prompt += f"Big blind: ${big_blind}\n"
        prompt += f"Number of players: {len(game_state.players)}\n\n"
        
        prompt += "Game rules:\n"
        prompt += "- Texas Hold'em\n"
        prompt += "- You will receive 2 hole cards\n"
        prompt += "- Community cards will be revealed (flop, turn, river)\n"
        prompt += "- Choose actions strategically based on odds and position\n"
        prompt += "- Last player with chips wins!\n\n"
        
        return prompt
    
    @staticmethod
    def _cards_to_string(cards: List[Tuple[str, str]]) -> str:
        """
        Convert cards to readable string.
        
        Args:
            cards: List of (rank, suit) tuples
        
        Returns:
            String like "As Kh Qd"
        """
        suit_map = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
        return ' '.join(f"{rank}{suit_map.get(suit, '?')}" 
                       for rank, suit in cards)
    
    @staticmethod
    def build_results_prompt(winner_name: str, winning_hand: str,
                            final_pot: int, players_summary: List[Dict]) -> str:
        """
        Build a summary of hand results for LLM reflection.
        
        Args:
            winner_name: Name of winning player
            winning_hand: Description of winning hand (e.g., "Pair of Kings")
            final_pot: Total pot amount
            players_summary: List of player results
        
        Returns:
            Formatted results string
        """
        prompt = "=== HAND COMPLETE ===\n\n"
        prompt += f"Winner: {winner_name}\n"
        prompt += f"Winning hand: {winning_hand}\n"
        prompt += f"Final pot: ${final_pot}\n\n"
        
        prompt += "Final stacks:\n"
        for player in players_summary:
            prompt += f"  {player['name']}: ${player['stack']}\n"
        
        return prompt
    
    @staticmethod
    def extract_action_from_response(response: str, legal_actions: List[str]) -> str:
        """
        Parse LLM response and extract the action.
        Handles various response formats.
        
        Args:
            response: Raw response from LLM
            legal_actions: List of legal actions for validation
        
        Returns:
            Parsed action string (or 'fold' if unparseable)
        """
        response = response.strip().lower()
        
        # Direct match
        for action in legal_actions:
            if action in response:
                return action
        
        # Handle "raise X" format
        if 'raise' in response:
            return 'raise'
        
        # Default to fold if nothing matches
        return 'fold'
    
    @staticmethod
    def _get_position(game_state: GameState, player_idx: int) -> Position:
        """Determine player's position based on table size and index."""
        num_players = len(game_state.players)
        
        if num_players == 2:
            # Heads-up
            return Position.BUTTON if player_idx == 0 else Position.BIG_BLIND
        elif num_players == 3:
            positions = [Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND]
            return positions[player_idx]
        else:
            # Assume button is at position 0
            button_offset = player_idx
            if button_offset == 0:
                return Position.BUTTON
            elif button_offset == 1:
                return Position.SMALL_BLIND
            elif button_offset == 2:
                return Position.BIG_BLIND
            elif button_offset <= num_players // 3:
                return Position.UTG
            elif button_offset <= 2 * num_players // 3:
                return Position.UTG_PLUS_1
            else:
                return Position.CUTOFF
    
    @staticmethod
    def _get_stack_depth(player_stack: int, game_state: GameState) -> StackDepth:
        """Categorize stack depth in big blinds (assuming BB=10)."""
        # Estimate big blind (rough estimate)
        bb = 10
        
        bb_depth = player_stack / bb if bb > 0 else player_stack
        
        if bb_depth < 20:
            return StackDepth.SHORT
        elif bb_depth < 100:
            return StackDepth.MEDIUM
        else:
            return StackDepth.DEEP
    
    @staticmethod
    def _calculate_pot_odds(game_state: GameState, player: Player) -> Optional[Dict]:
        """
        Calculate pot odds for the current player.
        
        Returns:
            Dict with 'ratio' and 'equity' needed, or None if no bet to call
        """
        amount_to_call = game_state.bet_to_match - player.round_contribution
        
        if amount_to_call <= 0:
            return None
        
        total_pot_after_call = game_state.pot + amount_to_call
        
        # Pot odds ratio
        ratio = total_pot_after_call / amount_to_call if amount_to_call > 0 else 0
        equity_needed = (100 / ratio) if ratio > 0 else 0
        
        return {
            'ratio': ratio,
            'equity': equity_needed,
            'amount_to_call': amount_to_call,
            'pot_after_call': total_pot_after_call
        }
    
    @staticmethod
    def _analyze_opponents(game_state: GameState, view: Dict, 
                          action_history: Optional[List[Dict]] = None) -> Dict[str, Dict]:
        """
        Analyze opponent tendencies from recent action history.
        
        Returns:
            Dict mapping opponent names to their statistics
        """
        stats = {}
        
        if not action_history:
            # Default stats for opponents
            for opp in view['players']:
                if opp['name'] != view.get('my_position'):
                    stats[opp['name']] = {
                        'aggression': 'Unknown',
                        'fold_rate': 'Unknown',
                        'actions': 0
                    }
            return stats
        
        # Count actions by player
        actions_by_player = {}
        for action in action_history[-20:]:  # Last 20 actions
            player_name = action['player']
            action_type = action['action'].split()[0].lower()
            
            if player_name not in actions_by_player:
                actions_by_player[player_name] = {
                    'fold': 0, 'check': 0, 'call': 0, 'raise': 0, 'total': 0
                }
            
            actions_by_player[player_name][action_type] += 1
            actions_by_player[player_name]['total'] += 1
        
        # Calculate tendencies
        for player_name, actions in actions_by_player.items():
            total = actions['total']
            if total > 0:
                fold_rate = f"{(actions['fold'] / total * 100):.0f}%"
                
                aggressive_actions = actions['raise'] + actions['check']
                aggression = "Aggressive" if aggressive_actions > total * 0.4 else \
                            "Passive" if aggressive_actions < total * 0.2 else \
                            "Balanced"
                
                stats[player_name] = {
                    'aggression': aggression,
                    'fold_rate': fold_rate,
                    'actions': total
                }
            else:
                stats[player_name] = {
                    'aggression': 'Unknown',
                    'fold_rate': 'Unknown',
                    'actions': 0
                }
        
        return stats
    
    @staticmethod
    def _get_strategic_advice(game_state: GameState, player: Player, 
                             position: Position, stack_depth: StackDepth,
                             legal_actions: List[str]) -> str:
        """Generate strategic considerations based on game context."""
        advice = ""
        
        # Position-based advice
        if position in [Position.BUTTON, Position.CUTOFF]:
            advice += "- You're in a strong position: consider wider range of hands\n"
        elif position in [Position.SMALL_BLIND, Position.BIG_BLIND]:
            advice += "- You're in the blinds: be cautious with weak hands\n"
        else:
            advice += "- You're in early position: play tight, premium hands only\n"
        
        # Stack depth advice
        if stack_depth == StackDepth.SHORT:
            advice += "- Short stack: consider push/fold strategy with premium hands\n"
        elif stack_depth == StackDepth.DEEP:
            advice += "- Deep stack: play patiently, look for value spots\n"
        else:
            advice += "- Medium stack: balance aggression and defense\n"
        
        # Board texture
        if len(game_state.board) > 0:
            high_cards = sum(1 for rank, _ in game_state.board if rank in ['A', 'K', 'Q'])
            if high_cards >= 2:
                advice += "- Dry board: many players will have missed\n"
            else:
                advice += "- Wet board: multiple draw possibilities exist\n"
        
        # Pot odds
        pot_odds = PromptBuilder._calculate_pot_odds(game_state, player)
        if pot_odds:
            if pot_odds['ratio'] > 3:
                advice += "- Excellent pot odds: defending wide is justified\n"
            elif pot_odds['ratio'] < 1.5:
                advice += "- Poor pot odds: only call with strong hands\n"
        
        return advice
