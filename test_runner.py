#!/usr/bin/env python3
"""Simple test runner to verify unit tests work."""

import sys
import os
import traceback
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def run_test_function(test_func, test_name):
    """Run a single test function and return result."""
    try:
        test_func()
        return True, None
    except Exception as e:
        return False, str(e)

def run_basic_model_tests():
    """Run basic tests for data models."""
    print("Running basic model tests...")
    
    # Import test modules
    try:
        from ai_browser_agent.models.task import Task, TaskStep, ExecutionPlan, TaskStatus
        from ai_browser_agent.models.action import Action, ActionType
        from ai_browser_agent.models.page_content import PageContent, WebElement
        from ai_browser_agent.models.config import BrowserConfig, SecurityConfig, AIModelConfig, AppConfig
        
        print("✓ All model imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test Task model
    try:
        task = Task(id="test-1", description="Test task")
        assert task.id == "test-1"
        assert task.status == TaskStatus.PENDING
        assert task.validate() is True
        
        task.update_status(TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS
        
        print("✓ Task model tests passed")
    except Exception as e:
        print(f"✗ Task model test failed: {e}")
        return False
    
    # Test Action model
    try:
        action = Action(id="action-1", type=ActionType.CLICK, target="#button")
        assert action.validate() is True
        assert action.requires_confirmation() is False
        
        action.mark_executed(success=True, result={"clicked": True})
        assert action.success is True
        
        print("✓ Action model tests passed")
    except Exception as e:
        print(f"✗ Action model test failed: {e}")
        return False
    
    # Test WebElement model
    try:
        element = WebElement(
            tag_name="button",
            attributes={"id": "test", "class": "btn"},
            text_content="Click me",
            is_clickable=True
        )
        assert element.id == "test"
        assert element.has_text("Click") is True
        assert element.validate() is True
        
        print("✓ WebElement model tests passed")
    except Exception as e:
        print(f"✗ WebElement model test failed: {e}")
        return False
    
    # Test PageContent model
    try:
        elements = [
            WebElement(tag_name="button", is_clickable=True),
            WebElement(tag_name="a", attributes={"href": "/test"})
        ]
        page = PageContent(
            url="https://test.com",
            title="Test Page",
            elements=elements
        )
        
        clickable = page.find_clickable_elements()
        assert len(clickable) == 1
        
        links = page.get_links()
        assert len(links) == 1
        
        print("✓ PageContent model tests passed")
    except Exception as e:
        print(f"✗ PageContent model test failed: {e}")
        return False
    
    # Test Config models
    try:
        browser_config = BrowserConfig(headless=False, timeout=30)
        assert browser_config.validate() is True
        
        security_config = SecurityConfig(require_confirmation_for_payments=True)
        assert security_config.validate() is True
        assert security_config.is_sensitive_domain("https://paypal.com") is True
        
        ai_config = AIModelConfig(primary_model="claude", claude_api_key="test")
        assert ai_config.validate() is True
        assert ai_config.is_model_available("claude") is True
        
        app_config = AppConfig(browser=browser_config, security=security_config, ai_model=ai_config)
        assert app_config.validate() is True
        
        print("✓ Config model tests passed")
    except Exception as e:
        print(f"✗ Config model test failed: {e}")
        return False
    
    return True

def run_browser_controller_tests():
    """Run basic tests for browser controller."""
    print("\nRunning browser controller tests...")
    
    try:
        from ai_browser_agent.controllers.browser_controller import BrowserController
        from ai_browser_agent.models.config import BrowserConfig
        
        print("✓ BrowserController import successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    try:
        config = BrowserConfig(headless=True, timeout=10)
        controller = BrowserController(config)
        
        assert controller.browser_config == config
        assert controller.driver is None
        assert controller.is_connected() is False
        
        print("✓ BrowserController initialization tests passed")
    except Exception as e:
        print(f"✗ BrowserController test failed: {e}")
        return False
    
    return True

def run_ai_interface_tests():
    """Run basic tests for AI interfaces."""
    print("\nRunning AI interface tests...")
    
    try:
        from ai_browser_agent.interfaces.ai_model_interface import ModelInterface, ModelRequest, ModelResponse
        from ai_browser_agent.interfaces.claude_model import ClaudeModel
        
        print("✓ AI interface imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    try:
        # Test ModelRequest
        request = ModelRequest(prompt="Test prompt", max_tokens=100)
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        
        # Test ModelResponse
        response = ModelResponse(
            content="Test response",
            confidence=0.8,
            tokens_used=50,
            model_name="test-model",
            metadata={}
        )
        assert response.content == "Test response"
        assert response.confidence == 0.8
        
        # Test ClaudeModel initialization
        claude = ClaudeModel("test-key", "claude-3-sonnet-20240229")
        assert claude.api_key == "test-key"
        assert claude.get_token_limit() == 200000
        
        tokens = claude.estimate_tokens("This is a test")
        assert isinstance(tokens, int)
        assert tokens > 0
        
        print("✓ AI interface tests passed")
    except Exception as e:
        print(f"✗ AI interface test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Browser Agent - Unit Test Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Run model tests
    if not run_basic_model_tests():
        all_passed = False
    
    # Run browser controller tests
    if not run_browser_controller_tests():
        all_passed = False
    
    # Run AI interface tests
    if not run_ai_interface_tests():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All basic tests PASSED!")
        print("Unit test implementation appears to be working correctly.")
    else:
        print("✗ Some tests FAILED!")
        print("Please check the error messages above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())