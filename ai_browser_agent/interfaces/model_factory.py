"""Factory for creating and managing AI model instances."""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from .ai_model_interface import ModelInterface
from .claude_model import ClaudeModel
from .openai_model import OpenAIModel
from .mock_model import MockModel
from ..models.config import AIModelConfig


logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported AI model types."""
    CLAUDE = "claude"
    OPENAI = "openai"
    MOCK = "mock"


class ModelFactory:
    """Factory for creating and managing AI model instances."""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        self._model_instances: Dict[str, ModelInterface] = {}
        self._availability_cache: Dict[str, bool] = {}
    
    def create_model(self, model_type: str, model_name: Optional[str] = None) -> Optional[ModelInterface]:
        """Create a model instance of the specified type."""
        try:
            model_type_enum = ModelType(model_type.lower())
        except ValueError:
            logger.error(f"Unsupported model type: {model_type}")
            return None
        
        # Use cached instance if available
        cache_key = f"{model_type}_{model_name or 'default'}"
        if cache_key in self._model_instances:
            return self._model_instances[cache_key]
        
        model_instance = None
        
        if model_type_enum == ModelType.CLAUDE:
            model_instance = self._create_claude_model(model_name)
        elif model_type_enum == ModelType.OPENAI:
            model_instance = self._create_openai_model(model_name)
        elif model_type_enum == ModelType.MOCK:
            model_instance = self._create_mock_model(model_name)
        
        if model_instance:
            self._model_instances[cache_key] = model_instance
        
        return model_instance
    
    def _create_claude_model(self, model_name: Optional[str] = None) -> Optional[ClaudeModel]:
        """Create a Claude model instance."""
        if not self.config.claude_api_key:
            logger.warning("Claude API key not configured")
            return None
        
        # Default Claude model
        if not model_name:
            model_name = "claude-3-sonnet-20240229"
        
        model_config = {
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout
        }
        
        try:
            return ClaudeModel(
                api_key=self.config.claude_api_key,
                model_name=model_name,
                config=model_config
            )
        except Exception as e:
            logger.error(f"Failed to create Claude model: {e}")
            return None
    
    def _create_openai_model(self, model_name: Optional[str] = None) -> Optional[OpenAIModel]:
        """Create an OpenAI model instance."""
        if not self.config.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return None
        
        # Default OpenAI model
        if not model_name:
            model_name = "gpt-4"
        
        model_config = {
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout
        }
        
        try:
            return OpenAIModel(
                api_key=self.config.openai_api_key,
                model_name=model_name,
                config=model_config
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI model: {e}")
            return None
    
    def _create_mock_model(self, model_name: Optional[str] = None) -> MockModel:
        """Create a mock model instance for testing."""
        if not model_name:
            model_name = "mock-model"
        
        model_config = {
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout
        }
        
        return MockModel(
            api_key="mock_key",
            model_name=model_name,
            config=model_config
        )
    
    async def get_available_models(self) -> List[str]:
        """Get list of available and working AI models."""
        available_models = []
        
        # Check Claude availability
        if self.config.claude_api_key:
            claude_model = self.create_model("claude")
            if claude_model and await self._check_model_availability(claude_model, "claude"):
                available_models.append("claude")
        
        # Check OpenAI availability
        if self.config.openai_api_key:
            openai_model = self.create_model("openai")
            if openai_model and await self._check_model_availability(openai_model, "openai"):
                available_models.append("openai")
        
        # Mock model is always available
        available_models.append("mock")
        
        return available_models
    
    async def _check_model_availability(self, model: ModelInterface, model_type: str) -> bool:
        """Check if a model is available and cache the result."""
        if model_type in self._availability_cache:
            return self._availability_cache[model_type]
        
        try:
            is_available = await model.check_availability()
            self._availability_cache[model_type] = is_available
            return is_available
        except Exception as e:
            logger.error(f"Error checking {model_type} availability: {e}")
            self._availability_cache[model_type] = False
            return False
    
    async def get_primary_model(self) -> Optional[ModelInterface]:
        """Get the primary AI model based on configuration."""
        primary_model = self.create_model(self.config.primary_model)
        
        if primary_model:
            # Check if primary model is available
            if await self._check_model_availability(primary_model, self.config.primary_model):
                return primary_model
            else:
                logger.warning(f"Primary model {self.config.primary_model} is not available")
        
        # Try fallback model if primary is not available
        if self.config.fallback_model:
            logger.info(f"Trying fallback model: {self.config.fallback_model}")
            fallback_model = self.create_model(self.config.fallback_model)
            
            if fallback_model and await self._check_model_availability(fallback_model, self.config.fallback_model):
                return fallback_model
        
        # If no configured models are available, use mock model for testing
        logger.warning("No configured AI models available, falling back to mock model for testing")
        return self.create_model("mock")
    
    async def get_best_available_model(self) -> Optional[ModelInterface]:
        """Get the best available AI model (tries primary first, then fallback)."""
        return await self.get_primary_model()
    
    def clear_cache(self):
        """Clear the availability cache to force re-checking."""
        self._availability_cache.clear()
    
    async def cleanup(self):
        """Clean up all model instances."""
        for model in self._model_instances.values():
            if hasattr(model, 'close'):
                try:
                    await model.close()
                except Exception as e:
                    logger.warning(f"Error closing model: {e}")
        
        self._model_instances.clear()
        self._availability_cache.clear()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about configured models."""
        return {
            "primary_model": self.config.primary_model,
            "fallback_model": self.config.fallback_model,
            "available_api_keys": {
                "claude": bool(self.config.claude_api_key),
                "openai": bool(self.config.openai_api_key)
            },
            "config": {
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout": self.config.timeout,
                "max_context_length": self.config.max_context_length
            },
            "cached_instances": list(self._model_instances.keys()),
            "availability_cache": self._availability_cache.copy()
        }