from typing import Dict, Optional
from llm_integration.llm_interface import LLMInterface


class ClaudeLLM(LLMInterface):
    """Claude model integration via Anthropic API."""
    
    def __init__(self, model_id: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None, **kwargs):
        """
        Initialize Claude LLM.
        
        Args:
            model_id: Claude model version
            api_key: Anthropic API key
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        """
        super().__init__(model_id, **kwargs)
        self.api_key = api_key
        self.conversation_history = []
        
        # Set defaults
        if 'temperature' not in self.config:
            self.config['temperature'] = 0.7
        if 'max_tokens' not in self.config:
            self.config['max_tokens'] = 500
    
    def get_action(self, game_state: Dict, prompt: str) -> str:
        """
        Get poker action from Claude.
        
        Args:
            game_state: Current game state
            prompt: Formatted prompt with context
        
        Returns:
            Action string
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
        
        response = client.messages.create(
            model=self.model_id,
            max_tokens=self.config['max_tokens'],
            temperature=self.config['temperature'],
            system=self.format_system_prompt(),
            messages=self.conversation_history
        )
        
        action = response.content[0].text.strip()
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": action
        })
        
        return action
    
    def format_system_prompt(self) -> str:
        """Claude system prompt for poker gameplay."""
        return """You are an expert poker player. You make strategic decisions based on:
- Your hole cards and the community cards
- The current bet and pot size
- Stack sizes and player positions
- Game theory and probability

Respond with ONLY the action you want to take: 'fold', 'check', 'call', or 'raise X' (where X is the amount).
Be concise and decisive."""
    
    def reset(self):
        """Clear conversation history for new game."""
        self.conversation_history = []


class GPT4LLM(LLMInterface):
    """GPT-4 model integration via OpenAI API."""
    
    def __init__(self, model_id: str = "gpt-4o", api_key: Optional[str] = None, **kwargs):
        """
        Initialize GPT-4 LLM.
        
        Args:
            model_id: OpenAI model version
            api_key: OpenAI API key
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        """
        super().__init__(model_id, **kwargs)
        self.api_key = api_key
        self.conversation_history = []
        
        if 'temperature' not in self.config:
            self.config['temperature'] = 0.7
        if 'max_tokens' not in self.config:
            self.config['max_tokens'] = 500
    
    def get_action(self, game_state: Dict, prompt: str) -> str:
        """Get poker action from GPT-4."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
        
        client = OpenAI(api_key=self.api_key)
        
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
        
        response = client.chat.completions.create(
            model=self.model_id,
            max_tokens=self.config['max_tokens'],
            temperature=self.config['temperature'],
            system=self.format_system_prompt(),
            messages=self.conversation_history
        )
        
        action = response.choices[0].message.content.strip()
        
        self.conversation_history.append({
            "role": "assistant",
            "content": action
        })
        
        return action
    
    def format_system_prompt(self) -> str:
        """GPT-4 system prompt for poker gameplay."""
        return """You are a world-class poker player with deep knowledge of game theory and probability.
Make optimal strategic decisions considering:
- Pot odds and expected value
- Position and player tendencies
- Bankroll management
- Risk vs. reward

Respond with ONLY the action: 'fold', 'check', 'call', or 'raise X'.
Be direct and concise."""
    
    def reset(self):
        """Clear conversation history for new game."""
        self.conversation_history = []


class RandomLLM(LLMInterface):
    """Random action player (for testing/benchmarking)."""
    
    def __init__(self, model_id: str = "random", **kwargs):
        """Initialize random player."""
        super().__init__(model_id, **kwargs)
    
    def get_action(self, game_state: Dict, prompt: str) -> str:
        """Return a random legal action."""
        import random
        legal_actions = game_state.get('legal_actions', ['fold'])
        return random.choice(legal_actions)
    
    def format_system_prompt(self) -> str:
        """No system prompt for random player."""
        return "Random action selection."
    
    def reset(self):
        """No state to reset."""
        pass


class CallAnyLLM(LLMInterface):
    """Calls all bets (for testing/benchmarking)."""
    
    def __init__(self, model_id: str = "call_any", **kwargs):
        """Initialize call-any player."""
        super().__init__(model_id, **kwargs)
    
    def get_action(self, game_state: Dict, prompt: str) -> str:
        """Always call."""
        legal_actions = game_state.get('legal_actions', ['fold'])
        if 'call' in legal_actions:
            return 'call'
        elif 'check' in legal_actions:
            return 'check'
        else:
            return 'fold'
    
    def format_system_prompt(self) -> str:
        """No system prompt."""
        return "Always call or check."
    
    def reset(self):
        """No state to reset."""
        pass


def create_llm(model_id: str, **kwargs) -> LLMInterface:
    """
    Factory function to create LLM instances.
    
    Args:
        model_id: Model identifier (e.g., 'claude-3-5-sonnet', 'gpt-4o', 'random')
        **kwargs: Model-specific configuration
    
    Returns:
        LLMInterface instance
    """
    if 'claude' in model_id.lower():
        return ClaudeLLM(model_id=model_id, **kwargs)
    elif 'gpt' in model_id.lower():
        return GPT4LLM(model_id=model_id, **kwargs)
    elif model_id.lower() == 'random':
        return RandomLLM(**kwargs)
    elif model_id.lower() == 'call_any':
        return CallAnyLLM(**kwargs)
    else:
        raise ValueError(f"Unknown model: {model_id}")
