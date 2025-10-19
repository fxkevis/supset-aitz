"""Claude AI model implementation."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import aiohttp
import tiktoken

from .ai_model_interface import ModelInterface, ModelRequest, ModelResponse


logger = logging.getLogger(__name__)


class ClaudeModel(ModelInterface):
    """Claude AI model implementation for Russian Federation access."""
    
    # Claude API endpoints that work in Russia
    CLAUDE_API_ENDPOINTS = [
        "https://api.anthropic.com/v1/messages",
        # Add alternative endpoints if needed for Russian access
    ]
    
    # Model configurations
    MODEL_CONFIGS = {
        "claude-3-sonnet-20240229": {
            "max_tokens": 200000,
            "context_window": 200000,
            "cost_per_token": 0.000003
        },
        "claude-3-haiku-20240307": {
            "max_tokens": 200000,
            "context_window": 200000,
            "cost_per_token": 0.00000025
        },
        "claude-3-opus-20240229": {
            "max_tokens": 200000,
            "context_window": 200000,
            "cost_per_token": 0.000015
        }
    }
    
    def __init__(self, api_key: str, model_name: str = "claude-3-sonnet-20240229", 
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, model_name, config)
        self.api_endpoint = self.config.get("api_endpoint", self.CLAUDE_API_ENDPOINTS[0])
        self.api_version = self.config.get("api_version", "2023-06-01")
        self.session = None
        
        # Initialize tokenizer for token estimation
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not initialize tokenizer: {e}")
            self.tokenizer = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": self.api_version
            }
            timeout = aiohttp.ClientTimeout(total=self.config.get("timeout", 30))
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from Claude API."""
        try:
            session = await self._get_session()
            
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "max_tokens": request.max_tokens or self.config.get("max_tokens", 4000),
                "messages": [
                    {
                        "role": "user",
                        "content": self._build_prompt(request)
                    }
                ]
            }
            
            # Add optional parameters
            if request.temperature is not None:
                payload["temperature"] = request.temperature
            elif "temperature" in self.config:
                payload["temperature"] = self.config["temperature"]
            
            if request.system_message:
                payload["system"] = request.system_message
            
            logger.debug(f"Sending request to Claude API: {self.api_endpoint}")
            
            async with session.post(self.api_endpoint, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data, request)
                else:
                    error_text = await response.text()
                    logger.error(f"Claude API error {response.status}: {error_text}")
                    raise Exception(f"Claude API error {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Error generating Claude response: {e}")
            # Return error response
            return ModelResponse(
                content=f"Error: {str(e)}",
                confidence=0.0,
                tokens_used=0,
                model_name=self.model_name,
                metadata={"error": str(e)}
            )
    
    def _build_prompt(self, request: ModelRequest) -> str:
        """Build the complete prompt from request components."""
        prompt_parts = []
        
        if request.context:
            prompt_parts.append(f"Context: {request.context}")
        
        prompt_parts.append(request.prompt)
        
        return "\n\n".join(prompt_parts)
    
    def _parse_response(self, data: Dict[str, Any], request: ModelRequest) -> ModelResponse:
        """Parse Claude API response into ModelResponse."""
        try:
            content = data["content"][0]["text"]
            
            # Extract usage information
            usage = data.get("usage", {})
            tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(content, data)
            
            return ModelResponse(
                content=content,
                confidence=confidence,
                tokens_used=tokens_used,
                model_name=self.model_name,
                metadata={
                    "usage": usage,
                    "model": data.get("model", self.model_name),
                    "stop_reason": data.get("stop_reason"),
                    "request_id": data.get("id")
                }
            )
        except KeyError as e:
            logger.error(f"Error parsing Claude response: {e}")
            return ModelResponse(
                content="Error parsing response",
                confidence=0.0,
                tokens_used=0,
                model_name=self.model_name,
                metadata={"error": f"Parse error: {e}"}
            )
    
    def _calculate_confidence(self, content: str, response_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on response characteristics."""
        confidence = 0.8  # Base confidence for successful response
        
        # Adjust based on content length
        if len(content) < 10:
            confidence -= 0.3
        elif len(content) > 100:
            confidence += 0.1
        
        # Adjust based on stop reason
        stop_reason = response_data.get("stop_reason")
        if stop_reason == "end_turn":
            confidence += 0.1
        elif stop_reason == "max_tokens":
            confidence -= 0.2
        
        return min(max(confidence, 0.0), 1.0)
    
    async def check_availability(self) -> bool:
        """Check if Claude API is available."""
        try:
            # Simple test request to check API availability
            test_request = ModelRequest(
                prompt="Hello",
                max_tokens=10
            )
            
            response = await self.generate_response(test_request)
            self.is_available = "error" not in response.metadata
            return self.is_available
            
        except Exception as e:
            logger.error(f"Claude availability check failed: {e}")
            self.is_available = False
            return False
    
    def get_token_limit(self) -> int:
        """Get the maximum token limit for this Claude model."""
        model_config = self.MODEL_CONFIGS.get(self.model_name)
        if model_config:
            return model_config["context_window"]
        return 200000  # Default for Claude-3 models
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the given text."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token estimation error: {e}")
        
        # Fallback: rough estimation (1 token ≈ 4 characters for English)
        return len(text) // 4
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.session and not self.session.closed:
            # Note: This is not ideal for async cleanup, but serves as a fallback
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except Exception:
                pass