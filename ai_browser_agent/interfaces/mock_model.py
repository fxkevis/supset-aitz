"""Mock AI model for testing and development."""

import logging
import asyncio
from typing import Dict, Any, Optional

from .ai_model_interface import ModelInterface, ModelRequest, ModelResponse


logger = logging.getLogger(__name__)


class MockModel(ModelInterface):
    """Mock AI model that provides simple responses for testing."""
    
    def __init__(self, api_key: str = "mock_key", model_name: str = "mock-model", config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, model_name, config)
        self.is_available = True
        self.token_limit = 4000
        
    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """Generate a mock response based on the request."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Generate a simple response based on the prompt
        response_content = self._generate_mock_response(request.prompt, request.context)
        
        # Estimate tokens used (rough approximation)
        tokens_used = len(response_content.split()) + len(request.prompt.split())
        
        return ModelResponse(
            content=response_content,
            confidence=0.8,
            tokens_used=tokens_used,
            model_name=self.model_name,
            metadata={
                "mock": True,
                "request_prompt": request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt
            }
        )
    
    def _generate_mock_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a mock response based on the prompt content."""
        prompt_lower = prompt.lower()
        
        # Navigation responses
        if "navigate" in prompt_lower and "google.com" in prompt_lower:
            return """{
    "decision": "navigate",
    "actions": [
        {
            "type": "navigate",
            "target": "https://www.google.com",
            "description": "Navigate to Google homepage",
            "confidence": 0.9
        }
    ],
    "reasoning": "User requested navigation to google.com, so I'll navigate to the Google homepage",
    "confidence": 0.9
}"""
        
        # General navigation
        if "navigate" in prompt_lower or "go to" in prompt_lower:
            return """{
    "decision": "navigate",
    "actions": [
        {
            "type": "navigate",
            "target": "url_from_context",
            "description": "Navigate to the specified URL",
            "confidence": 0.8
        }
    ],
    "reasoning": "User requested navigation to a URL",
    "confidence": 0.8
}"""
        
        # Page analysis
        if "analyze" in prompt_lower or "page content" in prompt_lower:
            return "I can see the page has loaded. The main elements include navigation, search functionality, and content areas."
        
        # Action planning
        if "plan" in prompt_lower or "steps" in prompt_lower:
            return "Based on the current page state, I recommend the following actions: 1) Identify target elements, 2) Execute the required interactions, 3) Verify the results."
        
        # Element interaction
        if "click" in prompt_lower or "button" in prompt_lower:
            return "I'll locate and click the specified element using the most reliable selector available."
        
        # Form filling
        if "fill" in prompt_lower or "form" in prompt_lower or "input" in prompt_lower:
            return "I'll fill out the form fields with the provided information, ensuring proper validation."
        
        # Email tasks
        if "email" in prompt_lower:
            return """{
    "decision": "compose_email",
    "actions": [
        {
            "type": "navigate",
            "target": "email_service",
            "description": "Navigate to email service",
            "confidence": 0.9
        },
        {
            "type": "click",
            "target": "compose_button",
            "description": "Click compose email button",
            "confidence": 0.8
        }
    ],
    "reasoning": "User wants to work with emails, I'll help them compose or manage emails",
    "confidence": 0.8
}"""
        
        # Messaging tasks
        if "send" in prompt_lower and "message" in prompt_lower:
            return """{
    "decision": "send_message",
    "actions": [
        {
            "type": "navigate",
            "target": "messaging_platform",
            "description": "Navigate to messaging platform",
            "confidence": 0.9
        },
        {
            "type": "search",
            "target": "contact_name",
            "description": "Search for contact",
            "confidence": 0.8
        },
        {
            "type": "type",
            "target": "message_content",
            "description": "Type and send message",
            "confidence": 0.9
        }
    ],
    "reasoning": "User wants to send a message to someone, I'll help them navigate to the platform and send the message",
    "confidence": 0.9
}"""
        
        # Shopping/ordering tasks
        if "order" in prompt_lower or "buy" in prompt_lower or "shopping" in prompt_lower:
            return """{
    "decision": "online_shopping",
    "actions": [
        {
            "type": "navigate",
            "target": "shopping_site",
            "description": "Navigate to shopping website",
            "confidence": 0.8
        },
        {
            "type": "search",
            "target": "product",
            "description": "Search for product",
            "confidence": 0.8
        }
    ],
    "reasoning": "User wants to shop or order something online",
    "confidence": 0.8
}"""
        
        # Error handling
        if "error" in prompt_lower or "failed" in prompt_lower:
            return "I understand there was an issue. Let me try an alternative approach or request clarification on how to proceed."
        
        # Default response
        return """{
    "decision": "wait",
    "actions": [
        {
            "type": "wait",
            "target": "user_input",
            "description": "Wait for more specific instructions",
            "confidence": 0.5
        }
    ],
    "reasoning": "Need more specific instructions to proceed",
    "confidence": 0.5
}"""
    
    async def check_availability(self) -> bool:
        """Mock model is always available."""
        return True
    
    def get_token_limit(self) -> int:
        """Return the mock token limit."""
        return self.token_limit
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens (rough approximation: ~4 characters per token)."""
        return len(text) // 4