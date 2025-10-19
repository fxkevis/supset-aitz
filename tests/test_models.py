"""Unit tests for data models."""

import pytest
from datetime import datetime
from ai_browser_agent.models.task import Task, TaskStep, ExecutionPlan, TaskStatus
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.page_content import PageContent, WebElement
from ai_browser_agent.models.config import BrowserConfig, SecurityConfig, AIModelConfig, AppConfig


class TestTask:
    """Test cases for Task model."""
    
    def test_task_creation(self, sample_task):
        """Test basic task creation."""
        assert sample_task.id == "test-task-1"
        assert sample_task.description == "Test task description"
        assert sample_task.status == TaskStatus.PENDING
        assert isinstance(sample_task.created_at, datetime)
    
    def test_task_validation(self, sample_task):
        """Test task validation."""
        assert sample_task.validate() is True
        
        # Test invalid task
        invalid_task = Task(id="", description="")
        assert invalid_task.validate() is False
    
    def test_update_status(self, sample_task):
        """Test status update functionality."""
        original_time = sample_task.updated_at
        sample_task.update_status(TaskStatus.IN_PROGRESS)
        
        assert sample_task.status == TaskStatus.IN_PROGRESS
        assert sample_task.updated_at > original_time
    
    def test_add_context(self, sample_task):
        """Test adding context to task."""
        sample_task.add_context("test_key", "test_value")
        assert sample_task.context["test_key"] == "test_value"
    
    def test_set_result(self, sample_task):
        """Test setting task result."""
        result = {"success": True, "data": "test"}
        sample_task.set_result(result)
        assert sample_task.result == result
    
    def test_set_error(self, sample_task):
        """Test setting task error."""
        error_msg = "Test error"
        sample_task.set_error(error_msg)
        
        assert sample_task.error_message == error_msg
        assert sample_task.status == TaskStatus.FAILED
        assert sample_task.completed_at is not None
    
    def test_progress_percentage(self, sample_task, sample_execution_plan):
        """Test progress percentage calculation."""
        sample_task.execution_plan = sample_execution_plan
        
        # No steps completed
        assert sample_task.get_progress_percentage() == 0.0
        
        # Complete first step
        sample_execution_plan.steps[0].mark_completed()
        assert sample_task.get_progress_percentage() == pytest.approx(33.33, rel=1e-2)
        
        # Complete all steps
        for step in sample_execution_plan.steps:
            step.mark_completed()
        assert sample_task.get_progress_percentage() == 100.0


class TestTaskStep:
    """Test cases for TaskStep model."""
    
    def test_task_step_creation(self, sample_task_step):
        """Test basic task step creation."""
        assert sample_task_step.id == "step-1"
        assert sample_task_step.description == "Test step"
        assert sample_task_step.action_type == "click"
        assert sample_task_step.is_completed is False
    
    def test_task_step_validation(self, sample_task_step):
        """Test task step validation."""
        assert sample_task_step.validate() is True
        
        # Test invalid step
        invalid_step = TaskStep(id="", description="", action_type="")
        assert invalid_step.validate() is False
    
    def test_mark_completed(self, sample_task_step):
        """Test marking step as completed."""
        execution_time = 1.5
        sample_task_step.mark_completed(execution_time)
        
        assert sample_task_step.is_completed is True
        assert sample_task_step.execution_time == execution_time
    
    def test_mark_failed(self, sample_task_step):
        """Test marking step as failed."""
        error_msg = "Step failed"
        sample_task_step.mark_failed(error_msg)
        
        assert sample_task_step.is_completed is False
        assert sample_task_step.error_message == error_msg


class TestExecutionPlan:
    """Test cases for ExecutionPlan model."""
    
    def test_execution_plan_creation(self, sample_execution_plan):
        """Test basic execution plan creation."""
        assert sample_execution_plan.task_id == "test-task"
        assert len(sample_execution_plan.steps) == 3
        assert sample_execution_plan.current_step_index == 0
    
    def test_current_step(self, sample_execution_plan):
        """Test getting current step."""
        current = sample_execution_plan.current_step
        assert current is not None
        assert current.id == "step-1"
    
    def test_advance_step(self, sample_execution_plan):
        """Test advancing to next step."""
        assert sample_execution_plan.advance_step() is True
        assert sample_execution_plan.current_step_index == 1
        
        # Advance to last step
        sample_execution_plan.advance_step()
        assert sample_execution_plan.current_step_index == 2
        
        # Cannot advance beyond last step
        assert sample_execution_plan.advance_step() is False
    
    def test_is_complete(self, sample_execution_plan):
        """Test completion check."""
        assert sample_execution_plan.is_complete() is False
        
        # Mark all steps as completed
        for step in sample_execution_plan.steps:
            step.mark_completed()
        
        assert sample_execution_plan.is_complete() is True
    
    def test_get_remaining_steps(self, sample_execution_plan):
        """Test getting remaining steps."""
        remaining = sample_execution_plan.get_remaining_steps()
        assert len(remaining) == 3
        
        # Complete first step
        sample_execution_plan.steps[0].mark_completed()
        remaining = sample_execution_plan.get_remaining_steps()
        assert len(remaining) == 2


class TestAction:
    """Test cases for Action model."""
    
    def test_action_creation(self, sample_action):
        """Test basic action creation."""
        assert sample_action.id == "action-1"
        assert sample_action.type == ActionType.CLICK
        assert sample_action.target == "#test-button"
        assert sample_action.is_destructive is False
    
    def test_action_validation(self, sample_action):
        """Test action validation."""
        assert sample_action.validate() is True
        
        # Test invalid action
        invalid_action = Action(id="", type=ActionType.CLICK, target="")
        assert invalid_action.validate() is False
        
        # Test action with invalid confidence
        invalid_confidence = Action(id="test", type=ActionType.CLICK, target="#btn", confidence=1.5)
        assert invalid_confidence.validate() is False
    
    def test_mark_executed(self, sample_action):
        """Test marking action as executed."""
        result = {"element_found": True}
        sample_action.mark_executed(success=True, result=result)
        
        assert sample_action.success is True
        assert sample_action.result == result
        assert sample_action.executed_at is not None
    
    def test_requires_confirmation(self, sample_action):
        """Test confirmation requirement check."""
        # Safe action should not require confirmation
        assert sample_action.requires_confirmation() is False
        
        # Destructive action should require confirmation
        destructive_action = Action(
            id="test", type=ActionType.CLICK, target="#btn", is_destructive=True
        )
        assert destructive_action.requires_confirmation() is True
        
        # Submit action should require confirmation
        submit_action = Action(id="test", type=ActionType.SUBMIT, target="form")
        assert submit_action.requires_confirmation() is True
    
    def test_to_dict_from_dict(self, sample_action):
        """Test serialization and deserialization."""
        action_dict = sample_action.to_dict()
        
        assert action_dict["id"] == sample_action.id
        assert action_dict["type"] == sample_action.type.value
        assert action_dict["target"] == sample_action.target
        
        # Test deserialization
        restored_action = Action.from_dict(action_dict)
        assert restored_action.id == sample_action.id
        assert restored_action.type == sample_action.type
        assert restored_action.target == sample_action.target


class TestWebElement:
    """Test cases for WebElement model."""
    
    def test_web_element_creation(self, sample_web_element):
        """Test basic web element creation."""
        assert sample_web_element.tag_name == "button"
        assert sample_web_element.id == "test-button"
        assert sample_web_element.class_name == "btn btn-primary"
        assert sample_web_element.is_clickable is True
    
    def test_has_text(self, sample_web_element):
        """Test text content checking."""
        assert sample_web_element.has_text("Click") is True
        assert sample_web_element.has_text("click") is True  # Case insensitive
        assert sample_web_element.has_text("NotFound") is False
    
    def test_get_attribute(self, sample_web_element):
        """Test attribute access."""
        assert sample_web_element.get_attribute("id") == "test-button"
        assert sample_web_element.get_attribute("nonexistent") is None
        assert sample_web_element.get_attribute("nonexistent", "default") == "default"
    
    def test_has_attribute(self, sample_web_element):
        """Test attribute existence check."""
        assert sample_web_element.has_attribute("id") is True
        assert sample_web_element.has_attribute("nonexistent") is False


class TestPageContent:
    """Test cases for PageContent model."""
    
    def test_page_content_creation(self, sample_page_content):
        """Test basic page content creation."""
        assert sample_page_content.url == "https://test.example.com"
        assert sample_page_content.title == "Test Page"
        assert len(sample_page_content.elements) == 3
    
    def test_find_elements_by_tag(self, sample_page_content):
        """Test finding elements by tag name."""
        buttons = sample_page_content.find_elements_by_tag("button")
        assert len(buttons) == 1
        assert buttons[0].tag_name == "button"
    
    def test_find_elements_by_text(self, sample_page_content):
        """Test finding elements by text content."""
        elements = sample_page_content.find_elements_by_text("Test")
        assert len(elements) >= 1  # Should find elements containing "Test"
    
    def test_find_clickable_elements(self, sample_page_content):
        """Test finding clickable elements."""
        clickable = sample_page_content.find_clickable_elements()
        assert len(clickable) == 1
        assert clickable[0].tag_name == "button"
    
    def test_get_links(self, sample_page_content):
        """Test getting link elements."""
        links = sample_page_content.get_links()
        assert len(links) == 1
        assert links[0].tag_name == "a"
        assert links[0].href == "/test"
    
    def test_get_summary(self, sample_page_content):
        """Test getting page summary."""
        summary = sample_page_content.get_summary()
        assert "Test Page" in summary
        assert "https://test.example.com" in summary
        assert "Elements: 3 total" in summary


class TestBrowserConfig:
    """Test cases for BrowserConfig model."""
    
    def test_browser_config_creation(self, browser_config):
        """Test basic browser config creation."""
        assert browser_config.headless is False
        assert browser_config.window_size == (1920, 1080)
        assert browser_config.timeout == 30
        assert browser_config.browser_type == "chrome"
    
    def test_browser_config_validation(self, browser_config):
        """Test browser config validation."""
        assert browser_config.validate() is True
        
        # Test invalid window size
        browser_config.window_size = (0, 1080)
        assert browser_config.validate() is False
        
        # Test invalid browser type
        browser_config.window_size = (1920, 1080)  # Reset
        browser_config.browser_type = "invalid"
        assert browser_config.validate() is False
    
    def test_to_selenium_options(self, browser_config):
        """Test conversion to Selenium options."""
        options = browser_config.to_selenium_options()
        
        assert options["headless"] is False
        assert options["window_size"] == (1920, 1080)
        assert options["page_load_timeout"] == 30


class TestSecurityConfig:
    """Test cases for SecurityConfig model."""
    
    def test_security_config_creation(self, security_config):
        """Test basic security config creation."""
        assert security_config.require_confirmation_for_payments is True
        assert security_config.require_confirmation_for_deletions is True
        assert security_config.max_task_duration == 3600
    
    def test_is_sensitive_domain(self, security_config):
        """Test sensitive domain detection."""
        assert security_config.is_sensitive_domain("https://paypal.com/checkout") is True
        assert security_config.is_sensitive_domain("https://example.com") is False
    
    def test_is_destructive_action(self, security_config):
        """Test destructive action detection."""
        assert security_config.is_destructive_action("Delete all emails") is True
        assert security_config.is_destructive_action("Purchase item") is True
        assert security_config.is_destructive_action("Read email") is False
    
    def test_requires_confirmation(self, security_config):
        """Test confirmation requirement logic."""
        # Payment action should require confirmation
        assert security_config.requires_confirmation(
            "payment", "https://example.com", "Make payment"
        ) is True
        
        # Sensitive domain should require confirmation
        assert security_config.requires_confirmation(
            "click", "https://paypal.com", "Click button"
        ) is True
        
        # Safe action should not require confirmation
        assert security_config.requires_confirmation(
            "read", "https://example.com", "Read content"
        ) is False


class TestAIModelConfig:
    """Test cases for AIModelConfig model."""
    
    def test_ai_model_config_creation(self, ai_model_config):
        """Test basic AI model config creation."""
        assert ai_model_config.primary_model == "claude"
        assert ai_model_config.claude_api_key == "test-key"
        assert ai_model_config.max_tokens == 4000
        assert ai_model_config.temperature == 0.7
    
    def test_get_available_models(self, ai_model_config):
        """Test getting available models."""
        available = ai_model_config.get_available_models()
        assert "claude" in available
        assert len(available) == 1
        
        # Add OpenAI key
        ai_model_config.openai_api_key = "openai-key"
        available = ai_model_config.get_available_models()
        assert "openai" in available
        assert len(available) == 2
    
    def test_is_model_available(self, ai_model_config):
        """Test model availability check."""
        assert ai_model_config.is_model_available("claude") is True
        assert ai_model_config.is_model_available("openai") is False
    
    def test_ai_model_config_validation(self, ai_model_config):
        """Test AI model config validation."""
        assert ai_model_config.validate() is True
        
        # Test invalid temperature
        ai_model_config.temperature = 3.0
        assert ai_model_config.validate() is False


class TestAppConfig:
    """Test cases for AppConfig model."""
    
    def test_app_config_creation(self, app_config):
        """Test basic app config creation."""
        assert isinstance(app_config.browser, BrowserConfig)
        assert isinstance(app_config.security, SecurityConfig)
        assert isinstance(app_config.ai_model, AIModelConfig)
    
    def test_app_config_validation(self, app_config):
        """Test app config validation."""
        assert app_config.validate() is True
        
        # Make one component invalid
        app_config.browser.timeout = -1
        assert app_config.validate() is False
    
    def test_to_dict_from_dict(self, app_config):
        """Test serialization and deserialization."""
        config_dict = app_config.to_dict()
        
        assert "browser" in config_dict
        assert "security" in config_dict
        assert "ai_model" in config_dict
        
        # Test loading from dict
        loaded_config = AppConfig.load_from_dict(config_dict)
        assert loaded_config.browser.timeout == app_config.browser.timeout
        assert loaded_config.security.max_task_duration == app_config.security.max_task_duration