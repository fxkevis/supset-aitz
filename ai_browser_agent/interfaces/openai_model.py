"""OpenAI model implementation as fallback option."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import aiohttp
import tiktoken

from .ai_model_interface import ModelInterface, ModelRequest, ModelResponse


logger = logging.getLogger(__name__)


class OpenAIModel(ModelInterface):
    """OpenAI model implementation as fallback option."""
    
    # OpenAI API configuration
    API_BASE_URL = "https://api.openai.com/v1"
    
    # Model configurations
    MODEL_CONFIGS = {
        "gpt-4": {
            "max_tokens": 8192,
            "context_window": 8192,
            "cost_per_token": 0.00003
        },
        "gpt-4-turbo": {
            "max_tokens": 4096,
            "context_window": 128000,
            "cost_per_token": 0.00001
        },
        "gpt-3.5-turbo": {
            "max_tokens": 4096,
            "context_window": 16385,
            "cost_per_token": 0.0000015
        },
        "gpt-3.5-turbo-16k": {
            "max_tokens": 4096,
            "context_window": 16385,
            "cost_per_token": 0.000003
        }
    }
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", 
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, model_name, config)
        self.api_base_url = self.config.get("api_base_url", self.API_BASE_URL)
        self.session = None
        
        # Initialize tokenizer for the specific model
        try:
            if "gpt-4" in model_name:
                self.tokenizer = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model_name:
                self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not initialize tokenizer for {model_name}: {e}")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            timeout = aiohttp.ClientTimeout(total=self.config.get("timeout", 30))
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from OpenAI API."""
        try:
            session = await self._get_session()
            
            # Prepare messages
            messages = []
            
            if request.system_message:
                messages.append({
                    "role": "system",
                    "content": request.system_message
                })
            
            # Build user message with context if provided
            user_content = self._build_prompt(request)
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.get("max_tokens", 4000),
            }
            
            # Add optional parameters
            if request.temperature is not None:
                payload["temperature"] = request.temperature
            elif "temperature" in self.config:
                payload["temperature"] = self.config["temperature"]
            
            # Add other optional parameters
            if "top_p" in self.config:
                payload["top_p"] = self.config["top_p"]
            if "frequency_penalty" in self.config:
                payload["frequency_penalty"] = self.config["frequency_penalty"]
            if "presence_penalty" in self.config:
                payload["presence_penalty"] = self.config["presence_penalty"]
            
            api_url = f"{self.api_base_url}/chat/completions"
            logger.debug(f"Sending request to OpenAI API: {api_url}")
            
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data, request)
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error {response.status}: {error_text}")
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
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
        """Parse OpenAI API response into ModelResponse."""
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            
            # Extract usage information
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(content, choice)
            
            return ModelResponse(
                content=content,
                confidence=confidence,
                tokens_used=tokens_used,
                model_name=self.model_name,
                metadata={
                    "usage": usage,
                    "model": data.get("model", self.model_name),
                    "finish_reason": choice.get("finish_reason"),
                    "request_id": data.get("id"),
                    "created": data.get("created")
                }
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing OpenAI response: {e}")
            return ModelResponse(
                content="Error parsing response",
                confidence=0.0,
                tokens_used=0,
                model_name=self.model_name,
                metadata={"error": f"Parse error: {e}"}
            )
    
    def _calculate_confidence(self, content: str, choice_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on response characteristics."""
        confidence = 0.8  # Base confidence for successful response
        
        # Adjust based on content length
        if len(content) < 10:
            confidence -= 0.3
        elif len(content) > 100:
            confidence += 0.1
        
        # Adjust based on finish reason
        finish_reason = choice_data.get("finish_reason")
        if finish_reason == "stop":
            confidence += 0.1
        elif finish_reason == "length":
            confidence -= 0.2
        elif finish_reason == "content_filter":
            confidence -= 0.4
        
        return min(max(confidence, 0.0), 1.0)
    
    async def check_availability(self) -> bool:
        """Check if OpenAI API is available."""
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
            logger.error(f"OpenAI availability check failed: {e}")
            self.is_available = False
            return False
    
    def get_token_limit(self) -> int:
        """Get the maximum token limit for this OpenAI model."""
        model_config = self.MODEL_CONFIGS.get(self.model_name)
        if model_config:
            return model_config["context_window"]
        return 4096  # Default fallback
    
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