from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class LLMInterface(ABC):
    """
    Abstract base class for LLM integrations.
    All LLM providers should inherit from this and implement the required methods.
    """
    
    def __init__(self, model_id: str, **kwargs):
        """
        Initialize the LLM interface.
        
        Args:
            model_id: Unique identifier for the model (e.g., 'claude-3-sonnet', 'gpt-4o')
            **kwargs: Additional configuration parameters
        """
        self.model_id = model_id
        self.config = kwargs
    
    @abstractmethod
    def get_action(self, game_state: Dict, prompt: str) -> str:
        """
        Ask the LLM for a poker action decision.
        
        Args:
            game_state: Current game state (from GameState.view_for())
            prompt: Formatted prompt with game context and available actions
        
        Returns:
            Action string ('fold', 'check', 'call', 'raise', or specific bet amount)
        """
        pass
    
    @abstractmethod
    def format_system_prompt(self) -> str:
        """
        Get the system prompt for this LLM.
        Defines the LLM's role and behavior in the poker game.
        
        Returns:
            System prompt string
        """
        pass
    
    def validate_action(self, action: str, legal_actions: List[str]) -> bool:
        """
        Validate that the LLM's action is legal.
        
        Args:
            action: Action string from LLM
            legal_actions: List of legal actions for the player
        
        Returns:
            True if action is legal, False otherwise
        """
        # Parse action (handle "raise X" format)
        action_type = action.split()[0].lower() if action else None
        return action_type in legal_actions
    
    def get_model_id(self) -> str:
        """Return the model ID."""
        return self.model_id
    
    def get_config(self) -> Dict:
        """Return the configuration dictionary."""
        return self.config
    
    @abstractmethod
    def reset(self):
        """Reset any session state (e.g., conversation history for multi-turn models)."""
        pass
