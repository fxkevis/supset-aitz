"""Interface for AI model interactions."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ModelResponse:
    """Response from an AI model."""
    content: str
    confidence: float
    tokens_used: int
    model_name: str
    metadata: Dict[str, Any]


@dataclass
class ModelRequest:
    """Request to an AI model."""
    prompt: str
    context: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_message: Optional[str] = None


class ModelInterface(ABC):
    """Abstract interface for AI model interactions."""
    
    def __init__(self, api_key: str, model_name: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.config = config or {}
        self.is_available = False
    
    @abstractmethod
    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the AI model."""
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """Check if the AI model is available."""
        pass
    
    @abstractmethod
    def get_token_limit(self) -> int:
        """Get the maximum token limit for this model."""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the given text."""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            "model_name": self.model_name,
            "is_available": self.is_available,
            "token_limit": self.get_token_limit(),
            "config": self.config
        }