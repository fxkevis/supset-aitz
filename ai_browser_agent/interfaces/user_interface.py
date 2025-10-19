"""Interface for user interactions."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Types of messages that can be displayed to the user."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    PROMPT = "prompt"
    STATUS = "status"


@dataclass
class UserMessage:
    """Message to be displayed to the user."""
    content: str
    message_type: MessageType
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UserPrompt:
    """Prompt for user input."""
    question: str
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    is_required: bool = True
    input_type: str = "text"  # text, choice, confirmation


class UserInterface(ABC):
    """Abstract interface for user interactions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_active = False
        self.message_history: List[UserMessage] = []
    
    @abstractmethod
    def display_message(self, message: UserMessage) -> None:
        """Display a message to the user."""
        pass
    
    @abstractmethod
    def get_user_input(self, prompt: UserPrompt) -> str:
        """Get input from the user."""
        pass
    
    @abstractmethod
    def display_status(self, status: Dict[str, Any]) -> None:
        """Display status information to the user."""
        pass
    
    @abstractmethod
    def start_interface(self) -> None:
        """Start the user interface."""
        pass
    
    @abstractmethod
    def stop_interface(self) -> None:
        """Stop the user interface."""
        pass
    
    def add_to_history(self, message: UserMessage) -> None:
        """Add a message to the history."""
        self.message_history.append(message)
    
    def get_message_history(self) -> List[UserMessage]:
        """Get the message history."""
        return self.message_history.copy()
    
    def clear_history(self) -> None:
        """Clear the message history."""
        self.message_history.clear()