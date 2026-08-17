from typing import List, Dict, Optional
from enum import Enum
import logging

from engine.deck import Deck
from engine.poker_state import GameState, Player
from engine.action_handler import ActionHandler
from engine.hand_evaluator import HandEvaluator
from llm_integration.llm_interface import LLMInterface
from llm_integration.prompt_builder import PromptBuilder
from game_management.game_config import GameConfig


class Street(Enum):
    """Poker betting rounds."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class GameRunner:
    """Orchestrates a complete poker hand."""
    
    def __init__(self, config: GameConfig, players_models: List[tuple], logger: Optional[logging.Logger] = None):
        """
        Initialize game runner.
        
        Args:
            config: GameConfig instance
            players_models: List of (player_name, llm_model) tuples
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or self._setup_logger()
        self.action_history = []
        self.hand_number = 0
        
        # Validate player count
        if len(players_models) != config.num_players:
            raise ValueError(f"Expected {config.num_players} players, got {len(players_models)}")
        
        # Create players
        self.players = [
            Player(name=name, stack=config.starting_stack, hand=[])
            for name, _ in players_models
        ]
        
        # Store LLM models
        self.llm_models: Dict[str, LLMInterface] = {
            players_models[i][0]: players_models[i][1] 
            for i in range(len(players_models))
        }
        
        self.game_state: Optional[GameState] = None
        self.deck: Optional[Deck] = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger."""
        logger = logging.getLogger('PokerRunner')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def run_hand(self, button_idx: int = 0) -> Optional[str]:
        """
        Run a complete hand of poker.
        
        Args:
            button_idx: Index of button/dealer position
        
        Returns:
            Name of winning player, or None if error
        """
        self.hand_number += 1
        self.action_history = []
        
        try:
            self.logger.info(f"=== HAND {self.hand_number} ===")
            self.logger.info(f"Button: {self.players[button_idx].name}")
            
            # Initialize deck and game state
            self.deck = Deck()
            self.game_state = GameState(players=self.players)
            
            # Collect blinds
            sb_idx = (button_idx + 1) % len(self.players)
            bb_idx = (button_idx + 2) % len(self.players)
            ActionHandler.collect_antes(self.game_state, self.config.small_blind, 
                                       self.config.big_blind, sb_idx, bb_idx)
            self.logger.info(f"Blinds collected: {self.players[sb_idx].name} posts ${self.config.small_blind}, "
                            f"{self.players[bb_idx].name} posts ${self.config.big_blind}")
            
            # Deal hole cards
            self._deal_hole_cards()
            
            # Set first to act (UTG)
            self.game_state.to_act = (bb_idx + 1) % len(self.players)
            
            # Preflop betting
            self._run_betting_street(Street.PREFLOP)
            
            # Check if only one player left (others folded)
            active = ActionHandler.get_active_players(self.game_state)
            if len(active) == 1:
                winner = active[0]
                self.logger.info(f"{winner.name} wins (others folded). Wins ${self.game_state.pot}")
                return winner.name
            
            # Flop
            flop = self.deck.deal(3)
            self.game_state.board = flop
            self.logger.info(f"Flop: {self.deck.cards_to_string(flop)}")
            ActionHandler.reset_round_for_next_street(self.game_state)
            self._run_betting_street(Street.FLOP)
            
            active = ActionHandler.get_active_players(self.game_state)
            if len(active) == 1:
                winner = active[0]
                self.logger.info(f"{winner.name} wins. Wins ${self.game_state.pot}")
                return winner.name
            
            # Turn
            turn = self.deck.deal(1)
            self.game_state.board.extend(turn)
            self.logger.info(f"Turn: {self.deck.cards_to_string(turn)}")
            ActionHandler.reset_round_for_next_street(self.game_state)
            self._run_betting_street(Street.TURN)
            
            active = ActionHandler.get_active_players(self.game_state)
            if len(active) == 1:
                winner = active[0]
                self.logger.info(f"{winner.name} wins. Wins ${self.game_state.pot}")
                return winner.name
            
            # River
            river = self.deck.deal(1)
            self.game_state.board.extend(river)
            self.logger.info(f"River: {self.deck.cards_to_string(river)}")
            ActionHandler.reset_round_for_next_street(self.game_state)
            self._run_betting_street(Street.RIVER)
            
            # Showdown
            return self._run_showdown()
        
        except Exception as e:
            self.logger.error(f"Error in hand: {e}", exc_info=True)
            return None
    
    def _deal_hole_cards(self):
        """Deal 2 cards to each player."""
        for player in self.players:
            if player.status != 'folded':
                cards = self.deck.deal(2)
                player.hand = cards
                if self.config.verbose:
                    self.logger.debug(f"{player.name} dealt {self.deck.cards_to_string(cards)}")
    
    def _run_betting_street(self, street: Street):
        """Run a complete betting street."""
        self.logger.info(f"--- {street.value.upper()} ---")
        
        active_players = ActionHandler.get_active_players(self.game_state)
        if len(active_players) <= 1:
            return
        
        # Loop until betting round complete
        while True:
            player = self.players[self.game_state.to_act]
            
            # Skip folded players
            if player.status == 'folded':
                ActionHandler.move_to_next_player(self.game_state)
                continue
            
            # Get action from LLM
            action = self._get_player_action(player, street)
            
            # Process action
            result = ActionHandler.process_action(self.game_state, player, action)
            
            if not result['success']:
                self.logger.warning(f"Invalid action from {player.name}: {action}. Error: {result['error']}")
                # Default to fold if invalid
                ActionHandler.process_action(self.game_state, player, 'fold')
                action = 'fold'
            
            # Log action
            self.logger.info(f"{player.name}: {action} (+${result['amount_added']})")
            self.action_history.append({
                'hand': self.hand_number,
                'street': street.value,
                'player': player.name,
                'action': action,
                'amount': result['amount_added'],
                'pot': self.game_state.pot
            })
            
            # Move to next player
            next_player_idx = ActionHandler.move_to_next_player(self.game_state)
            
            if next_player_idx is None:
                break
            
            # Check if betting round is complete
            if ActionHandler.is_betting_round_complete(self.game_state):
                break
    
    def _get_player_action(self, player: Player, street: Street) -> str:
        """Get action from player's LLM model."""
        llm_model = self.llm_models[player.name]
        view = self.game_state.view_for(player)
        prompt = PromptBuilder.build_player_prompt(self.game_state, player, self.action_history)
        
        try:
            action = llm_model.get_action(view, prompt)
            return action
        except Exception as e:
            self.logger.error(f"Error getting action from {player.name}: {e}")
            return 'fold'
    
    def _run_showdown(self) -> Optional[str]:
        """Determine winner at showdown."""
        self.logger.info("--- SHOWDOWN ---")
        
        active_players = ActionHandler.get_active_players(self.game_state)
        
        if len(active_players) == 0:
            self.logger.error("No active players at showdown")
            return None
        
        if len(active_players) == 1:
            winner = active_players[0]
            self.logger.info(f"{winner.name} wins (all others folded). Wins ${self.game_state.pot}")
            return winner.name
        
        # Evaluate all hands
        evaluated_hands = []
        for player in active_players:
            hand_eval = HandEvaluator.evaluate_hand(player.hand, self.game_state.board)
            evaluated_hands.append((player, hand_eval))
            self.logger.info(f"{player.name}: {hand_eval[1]} ({self.deck.cards_to_string(player.hand)})")
        
        # Determine winner
        winner = evaluated_hands[0][0]
        for player, hand_eval in evaluated_hands[1:]:
            cmp = HandEvaluator.compare_hands(evaluated_hands[0][1], hand_eval)
            if cmp < 0:
                winner = player
                evaluated_hands[0] = (player, hand_eval)
        
        # Update stacks
        winner.stack += self.game_state.pot
        self.logger.info(f"\n{winner.name} wins ${self.game_state.pot} with {evaluated_hands[0][1][1]}")
        
        return winner.name
    
    def get_player_stats(self) -> Dict:
        """Get current player statistics."""
        return {
            player.name: {
                'stack': player.stack,
                'hands_played': sum(1 for h in self.action_history if h['player'] == player.name),
            }
            for player in self.players
        }
