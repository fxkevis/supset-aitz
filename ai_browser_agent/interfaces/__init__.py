"""Base interfaces and abstract classes for the AI Browser Agent."""

from .base_interfaces import (
    BaseAgent,
    BaseController,
    BaseManager,
    BaseInterface,
    BaseValidator,
)
from .ai_model_interface import ModelInterface, ModelRequest, ModelResponse
from .claude_model import ClaudeModel
from .openai_model import OpenAIModel
from .model_factory import ModelFactory, ModelType
from .user_interface import UserInterface

__all__ = [
    "BaseAgent",
    "BaseController", 
    "BaseManager",
    "BaseInterface",
    "BaseValidator",
    "ModelInterface",
    "ModelRequest",
    "ModelResponse",
    "ClaudeModel",
    "OpenAIModel",
    "ModelFactory",
    "ModelType",
    "UserInterface",
]