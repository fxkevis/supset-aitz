"""Unit tests for AI integration components."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from ai_browser_agent.interfaces.ai_model_interface import ModelInterface, ModelRequest, ModelResponse
from ai_browser_agent.interfaces.claude_model import ClaudeModel
from ai_browser_agent.core.decision_engine import DecisionEngine
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.page_content import PageContent, WebElement
from ai_browser_agent.models.config import SecurityConfig


class TestModelInterface:
    """Test cases for ModelInterface abstract class."""
    
    def test_model_interface_initialization(self):
        """Test ModelInterface initialization."""
        # Create a concrete implementation for testing
        class TestModel(ModelInterface):
            async def generate_response(self, request):
                return ModelResponse("test", 0.8, 100, "test-model", {})
            
            async def check_availability(self):
                return True
            
            def get_token_limit(self):
                return 4000
            
            def estimate_tokens(self, text):
                return len(text) // 4
        
        model = TestModel("test-key", "test-model", {"param": "value"})
        
        assert model.api_key == "test-key"
        assert model.model_name == "test-model"
        assert model.config == {"param": "value"}
        assert model.is_available is False
    
    def test_get_model_info(self):
        """Test getting model information."""
        class TestModel(ModelInterface):
            async def generate_response(self, request):
                return ModelResponse("test", 0.8, 100, "test-model", {})
            
            async def check_availability(self):
                return True
            
            def get_token_limit(self):
                return 4000
            
            def estimate_tokens(self, text):
                return len(text) // 4
        
        model = TestModel("test-key", "test-model")
        info = model.get_model_info()
        
        assert info["model_name"] == "test-model"
        assert info["is_available"] is False
        assert info["token_limit"] == 4000


class TestModelRequest:
    """Test cases for ModelRequest data class."""
    
    def test_model_request_creation(self):
        """Test ModelRequest creation."""
        request = ModelRequest(
            prompt="Test prompt",
            context="Test context",
            max_tokens=1000,
            temperature=0.7,
            system_message="System message"
        )
        
        assert request.prompt == "Test prompt"
        assert request.context == "Test context"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7
        assert request.system_message == "System message"
    
    def test_model_request_defaults(self):
        """Test ModelRequest with default values."""
        request = ModelRequest(prompt="Test prompt")
        
        assert request.prompt == "Test prompt"
        assert request.context is None
        assert request.max_tokens is None
        assert request.temperature is None
        assert request.system_message is None


class TestModelResponse:
    """Test cases for ModelResponse data class."""
    
    def test_model_response_creation(self):
        """Test ModelResponse creation."""
        response = ModelResponse(
            content="Test response",
            confidence=0.85,
            tokens_used=150,
            model_name="test-model",
            metadata={"key": "value"}
        )
        
        assert response.content == "Test response"
        assert response.confidence == 0.85
        assert response.tokens_used == 150
        assert response.model_name == "test-model"
        assert response.metadata == {"key": "value"}


class TestClaudeModel:
    """Test cases for ClaudeModel."""
    
    @pytest.fixture
    def claude_model(self):
        """Create a ClaudeModel instance for testing."""
        return ClaudeModel("test-api-key", "claude-3-sonnet-20240229")
    
    def test_claude_model_initialization(self, claude_model):
        """Test ClaudeModel initialization."""
        assert claude_model.api_key == "test-api-key"
        assert claude_model.model_name == "claude-3-sonnet-20240229"
        assert claude_model.api_endpoint in claude_model.CLAUDE_API_ENDPOINTS
        assert claude_model.api_version == "2023-06-01"
    
    def test_get_token_limit(self, claude_model):
        """Test getting token limit."""
        limit = claude_model.get_token_limit()
        assert limit == 200000  # Claude-3 Sonnet limit
    
    def test_estimate_tokens(self, claude_model):
        """Test token estimation."""
        text = "This is a test text for token estimation."
        tokens = claude_model.estimate_tokens(text)
        
        # Should return a reasonable estimate
        assert isinstance(tokens, int)
        assert tokens > 0
        assert tokens < len(text)  # Should be less than character count
    
    def test_build_prompt(self, claude_model):
        """Test prompt building."""
        request = ModelRequest(
            prompt="Main prompt",
            context="Context information"
        )
        
        prompt = claude_model._build_prompt(request)
        
        assert "Context: Context information" in prompt
        assert "Main prompt" in prompt
    
    def test_calculate_confidence(self, claude_model):
        """Test confidence calculation."""
        # Test with good response
        good_response = {
            "stop_reason": "end_turn"
        }
        confidence = claude_model._calculate_confidence("Good response content", good_response)
        assert 0.8 <= confidence <= 1.0
        
        # Test with truncated response
        truncated_response = {
            "stop_reason": "max_tokens"
        }
        confidence = claude_model._calculate_confidence("Short", truncated_response)
        assert confidence < 0.8
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, claude_model):
        """Test error handling in generate_response."""
        request = ModelRequest(prompt="Test prompt")
        
        # Mock session to raise an exception
        with patch.object(claude_model, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.post.side_effect = Exception("Network error")
            mock_get_session.return_value = mock_session
            
            response = await claude_model.generate_response(request)
            
            assert "Error:" in response.content
            assert response.confidence == 0.0
            assert "error" in response.metadata
    
    def test_parse_response_success(self, claude_model):
        """Test successful response parsing."""
        api_response = {
            "content": [{"text": "Test response content"}],
            "usage": {"input_tokens": 50, "output_tokens": 100},
            "model": "claude-3-sonnet-20240229",
            "stop_reason": "end_turn",
            "id": "test-request-id"
        }
        
        request = ModelRequest(prompt="Test")
        response = claude_model._parse_response(api_response, request)
        
        assert response.content == "Test response content"
        assert response.tokens_used == 150
        assert response.model_name == "claude-3-sonnet-20240229"
        assert response.metadata["request_id"] == "test-request-id"
    
    def test_parse_response_error(self, claude_model):
        """Test response parsing with malformed data."""
        malformed_response = {"invalid": "structure"}
        
        request = ModelRequest(prompt="Test")
        response = claude_model._parse_response(malformed_response, request)
        
        assert response.content == "Error parsing response"
        assert response.confidence == 0.0
        assert "error" in response.metadata


class TestDecisionEngine:
    """Test cases for DecisionEngine."""
    
    @pytest.fixture
    def mock_model_factory(self):
        """Create a mock ModelFactory."""
        factory = Mock()
        mock_model = Mock(spec=ModelInterface)
        mock_model.generate_response = AsyncMock()
        factory.get_best_available_model = AsyncMock(return_value=mock_model)
        return factory
    
    @pytest.fixture
    def decision_engine(self, mock_model_factory, security_config):
        """Create a DecisionEngine instance for testing."""
        return DecisionEngine(mock_model_factory, security_config)
    
    def test_decision_engine_initialization(self, decision_engine, mock_model_factory, security_config):
        """Test DecisionEngine initialization."""
        assert decision_engine.model_factory == mock_model_factory
        assert decision_engine.security_config == security_config
        assert decision_engine.current_model is None
        assert decision_engine.decision_history == []
    
    def test_build_system_prompt(self, decision_engine):
        """Test system prompt building."""
        prompt = decision_engine._build_system_prompt()
        
        assert "AI browser automation agent" in prompt
        assert "safety" in prompt.lower()
        assert "JSON" in prompt
    
    def test_extract_page_summary(self, decision_engine, sample_page_content):
        """Test page summary extraction."""
        summary = decision_engine._extract_page_summary(sample_page_content)
        
        assert sample_page_content.url in summary
        assert sample_page_content.title in summary
        assert "Elements:" in summary
        assert "Clickable elements:" in summary
    
    def test_build_context_info(self, decision_engine, sample_task):
        """Test context information building."""
        context = {
            "previous_actions": [
                {"type": "click", "description": "Clicked button"},
                {"type": "type", "description": "Typed text"}
            ],
            "user_preferences": {"speed": "fast"},
            "session_info": {"logged_in": True, "current_domain": "example.com"}
        }
        
        context_info = decision_engine._build_context_info(sample_task, context)
        
        assert "Recent actions:" in context_info
        assert "User preferences:" in context_info
        assert "Logged in: True" in context_info
    
    def test_create_action_from_data(self, decision_engine):
        """Test creating Action from parsed data."""
        action_data = {
            "action_type": "click",
            "target": "#test-button",
            "parameters": {"wait": True},
            "description": "Click the test button",
            "confidence": 0.9,
            "is_destructive": False
        }
        
        action = decision_engine._create_action_from_data(action_data, 0.8)
        
        assert action is not None
        assert action.type == ActionType.CLICK
        assert action.target == "#test-button"
        assert action.parameters == {"wait": True}
        assert action.description == "Click the test button"
        assert action.confidence == 0.8  # Should use base confidence (lower)
        assert action.is_destructive is False
    
    def test_create_action_from_data_invalid_type(self, decision_engine):
        """Test creating Action with invalid action type."""
        action_data = {
            "action_type": "invalid_type",
            "target": "#test",
            "description": "Invalid action"
        }
        
        action = decision_engine._create_action_from_data(action_data, 0.8)
        
        assert action is None
    
    def test_validate_actions_security(self, decision_engine):
        """Test security validation of actions."""
        actions = [
            Action(
                id="1",
                type=ActionType.CLICK,
                target="#safe-button",
                description="Safe click action"
            ),
            Action(
                id="2",
                type=ActionType.SUBMIT,
                target="#payment-form",
                description="Submit payment form"
            )
        ]
        
        validated = decision_engine._validate_actions_security(actions, "https://paypal.com/checkout")
        
        assert len(validated) == 2
        # Payment form submission should be marked as destructive
        assert validated[1].is_destructive is True
        # Actions on sensitive domain should have reduced confidence
        assert all(action.confidence <= 0.8 for action in validated)
    
    def test_create_fallback_action(self, decision_engine):
        """Test creating fallback action."""
        error_msg = "Test error message"
        action = decision_engine._create_fallback_action(error_msg)
        
        assert action.type == ActionType.WAIT
        assert action.target == "body"
        assert action.confidence == 0.1
        assert error_msg in action.description
        assert action.is_destructive is False
    
    @pytest.mark.asyncio
    async def test_analyze_page_and_decide_success(self, decision_engine, sample_page_content, sample_task):
        """Test successful page analysis and decision making."""
        # Mock AI response
        ai_response = ModelResponse(
            content=json.dumps([{
                "action_type": "click",
                "target": "#test-button",
                "description": "Click test button",
                "confidence": 0.9,
                "is_destructive": False
            }]),
            confidence=0.85,
            tokens_used=200,
            model_name="test-model",
            metadata={}
        )
        
        decision_engine.current_model = Mock(spec=ModelInterface)
        decision_engine.current_model.generate_response = AsyncMock(return_value=ai_response)
        
        actions = await decision_engine.analyze_page_and_decide(sample_page_content, sample_task, {})
        
        assert len(actions) == 1
        assert actions[0].type == ActionType.CLICK
        assert actions[0].target == "#test-button"
        assert len(decision_engine.decision_history) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_page_and_decide_no_model(self, decision_engine, sample_page_content, sample_task):
        """Test decision making when no AI model is available."""
        decision_engine.model_factory.get_best_available_model = AsyncMock(return_value=None)
        
        actions = await decision_engine.analyze_page_and_decide(sample_page_content, sample_task, {})
        
        # Should return fallback action
        assert len(actions) == 1
        assert actions[0].type == ActionType.WAIT
        assert actions[0].confidence == 0.1
    
    @pytest.mark.asyncio
    async def test_analyze_page_and_decide_json_parse_error(self, decision_engine, sample_page_content, sample_task):
        """Test handling of JSON parse errors in AI response."""
        # Mock AI response with invalid JSON
        ai_response = ModelResponse(
            content="This is not valid JSON",
            confidence=0.8,
            tokens_used=100,
            model_name="test-model",
            metadata={}
        )
        
        decision_engine.current_model = Mock(spec=ModelInterface)
        decision_engine.current_model.generate_response = AsyncMock(return_value=ai_response)
        
        actions = await decision_engine.analyze_page_and_decide(sample_page_content, sample_task, {})
        
        # Should return fallback action due to parse error
        assert len(actions) == 1
        assert actions[0].type == ActionType.WAIT
    
    def test_extract_action_from_text(self, decision_engine):
        """Test extracting action from natural language text."""
        # Test click extraction
        click_action = decision_engine._extract_action_from_text("Please click the button", 0.8)
        assert click_action is not None
        assert click_action.type == ActionType.CLICK
        assert click_action.confidence == 0.4  # 0.8 * 0.5
        
        # Test type extraction
        type_action = decision_engine._extract_action_from_text("Type some text in the field", 0.8)
        assert type_action is not None
        assert type_action.type == ActionType.TYPE
        
        # Test no match
        no_action = decision_engine._extract_action_from_text("Just some random text", 0.8)
        assert no_action is None
    
    @pytest.mark.asyncio
    async def test_evaluate_action_success(self, decision_engine, sample_page_content):
        """Test action success evaluation."""
        action = Action(
            id="test",
            type=ActionType.NAVIGATE,
            target="https://example.com",
            description="Navigate to example.com"
        )
        
        # Mock AI response for evaluation
        eval_response = ModelResponse(
            content=json.dumps({
                "success": True,
                "confidence": 0.9,
                "reasoning": "URL changed successfully"
            }),
            confidence=0.8,
            tokens_used=100,
            model_name="test-model",
            metadata={}
        )
        
        decision_engine.current_model = Mock(spec=ModelInterface)
        decision_engine.current_model.generate_response = AsyncMock(return_value=eval_response)
        
        success, confidence, reasoning = await decision_engine.evaluate_action_success(
            action, sample_page_content, "Should navigate to example.com"
        )
        
        assert success is True
        assert confidence == 0.9
        assert "URL changed successfully" in reasoning
    
    def test_simple_success_evaluation(self, decision_engine, sample_page_content):
        """Test simple heuristic success evaluation."""
        # Test navigation action
        nav_action = Action(id="1", type=ActionType.NAVIGATE, target="https://test.example.com", description="Navigate")
        success, confidence, reasoning = decision_engine._simple_success_evaluation(nav_action, sample_page_content)
        assert success is True  # URL matches
        assert confidence == 0.7
        
        # Test click action
        click_action = Action(id="2", type=ActionType.CLICK, target="#button", description="Click")
        success, confidence, reasoning = decision_engine._simple_success_evaluation(click_action, sample_page_content)
        assert success is True  # Page has elements
        assert confidence == 0.6
    
    def test_decision_history_management(self, decision_engine):
        """Test decision history management."""
        # Test getting empty history
        history = decision_engine.get_decision_history()
        assert history == []
        
        # Add some mock decisions
        for i in range(15):
            decision_engine.decision_history.append({"decision": f"test_{i}"})
        
        # Test getting limited history
        recent = decision_engine.get_decision_history(5)
        assert len(recent) == 5
        assert recent[-1]["decision"] == "test_14"
        
        # Test clearing history
        decision_engine.clear_decision_history()
        assert decision_engine.decision_history == []