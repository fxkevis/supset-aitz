"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from ai_browser_agent.models.task import Task, TaskStep, ExecutionPlan, TaskStatus
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.page_content import PageContent, WebElement
from ai_browser_agent.models.config import AppConfig, BrowserConfig, SecurityConfig, AIModelConfig


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test-task-1",
        description="Test task description",
        status=TaskStatus.PENDING
    )


@pytest.fixture
def sample_task_step():
    """Create a sample task step for testing."""
    return TaskStep(
        id="step-1",
        description="Test step",
        action_type="click",
        parameters={"selector": "#test-button"}
    )


@pytest.fixture
def sample_execution_plan():
    """Create a sample execution plan for testing."""
    steps = [
        TaskStep(id="step-1", description="Navigate", action_type="navigate"),
        TaskStep(id="step-2", description="Click", action_type="click"),
        TaskStep(id="step-3", description="Type", action_type="type")
    ]
    return ExecutionPlan(task_id="test-task", steps=steps)


@pytest.fixture
def sample_action():
    """Create a sample action for testing."""
    return Action(
        id="action-1",
        type=ActionType.CLICK,
        target="#test-button",
        description="Click test button"
    )


@pytest.fixture
def sample_web_element():
    """Create a sample web element for testing."""
    return WebElement(
        tag_name="button",
        attributes={"id": "test-button", "class": "btn btn-primary"},
        text_content="Click me",
        css_selector="#test-button",
        is_clickable=True
    )


@pytest.fixture
def sample_page_content():
    """Create a sample page content for testing."""
    elements = [
        WebElement(tag_name="h1", text_content="Test Page"),
        WebElement(tag_name="button", attributes={"id": "btn1"}, is_clickable=True),
        WebElement(tag_name="a", attributes={"href": "/test"}, text_content="Test Link")
    ]
    return PageContent(
        url="https://test.example.com",
        title="Test Page",
        text_content="This is a test page",
        elements=elements
    )


@pytest.fixture
def browser_config():
    """Create a sample browser configuration."""
    return BrowserConfig(
        headless=False,
        window_size=(1920, 1080),
        timeout=30,
        browser_type="chrome"
    )


@pytest.fixture
def security_config():
    """Create a sample security configuration."""
    return SecurityConfig(
        require_confirmation_for_payments=True,
        require_confirmation_for_deletions=True,
        max_task_duration=3600
    )


@pytest.fixture
def ai_model_config():
    """Create a sample AI model configuration."""
    return AIModelConfig(
        primary_model="claude",
        claude_api_key="test-key",
        max_tokens=4000,
        temperature=0.7
    )


@pytest.fixture
def app_config(browser_config, security_config, ai_model_config):
    """Create a sample app configuration."""
    return AppConfig(
        browser=browser_config,
        security=security_config,
        ai_model=ai_model_config
    )


@pytest.fixture
def mock_webdriver():
    """Create a mock WebDriver for testing."""
    driver = Mock()
    driver.get = Mock()
    driver.find_element = Mock()
    driver.find_elements = Mock(return_value=[])
    driver.quit = Mock()
    driver.current_url = "https://test.example.com"
    driver.title = "Test Page"
    driver.page_source = "<html><body>Test</body></html>"
    return driver


@pytest.fixture
def mock_ai_model():
    """Create a mock AI model for testing."""
    model = Mock()
    model.generate_response = Mock(return_value="Test AI response")
    model.analyze_content = Mock(return_value={"action": "click", "target": "#button"})
    return model